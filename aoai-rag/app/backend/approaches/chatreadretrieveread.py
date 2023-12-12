import logging
from typing import Any, AsyncGenerator

import openai
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import QueryType

from core.messagebuilder import MessageBuilder
from core.modelhelper import get_token_limit
from text import nonewlines

class ChatReadRetrieveReadApproach:
    """
    Azure AI Search（旧 Azure Cognitive Search）と OpenAI の Python SDK を使用した、シンプルな retrieve-then-read の実装です。これは、最初に
    GPT を利用して検索クエリーを生成し、次に検索エンジンからトップ文書を抽出し、その検索結果を使ってプロンプトを構成して GPT で補完生成する (answer) サンプルコードです。
    """

    # Chat roles
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

    # System prompt
    system_message_chat_conversation = """
日本の鎌倉時代の歴史に関する読解問題に答えるアシスタントです。
If you cannot guess the answer to a question from the SOURCE, answer "I don't know".
Answers must be in Japanese.

# Restrictions
- The SOURCE prefix has a colon and actual information after the filename, and each fact used in the response must include the name of the source.
- To reference a source, use a square bracket. For example, [info1.txt]. Do not combine sources, but list each source separately. For example, [info1.txt][info2.pdf].

{follow_up_questions_prompt}
{injected_prompt}
"""
    # Follow-up question prompt
    follow_up_questions_prompt_content = """
回答には、ユーザーの質問に対する追加の3つのフォローアップ質問を添付する必要があります。フォローアップ質問のルールは「制限事項」に定義されています。

- Please answer only questions related to the history of the Kamakura period in Japan. If the question is not related to the history of the Kamakura period in Japan, answer "I don't know".
- Use double angle brackets to reference the questions, e.g. <<What did Minamotono Yoritomo do? >>.
- Try not to repeat questions that have already been asked.
- Do not add SOURCES to follow-up questions.
- Do not use bulleted follow-up questions. Always enclose them in double angle brackets.
- Follow-up questions should be ideas that expand the user's curiosity.
- Only generate questions and do not generate any text before or after the questions, such as 'Next Questions'

EXAMPLE:###
Q:徳川家康はどのような人物ですか？
A:徳川家康は、日本の戦国時代から江戸時代初期にかけての武将、大名、政治家であり、江戸幕府を開いた人物です。彼は義を重んじ、家来のことを大切にした人物とされています。また、負けず嫌いで血気盛んだったが、臆病だが冷静に対処できる性格だったとされています。 [徳川家康 - Wikipedia-2.pdf.txt][徳川家康 - Wikipedia-13.pdf][徳川家康-2.txt]<<徳川家康はどのような功績を残しましたか？>><<徳川家康はどのように江戸幕府を開いたのですか？>><<他にも有名な武将や大名はいますか？>>

Q:関ケ原の戦いはどのような戦いですか？
A:関ヶ原の戦いは、1600年10月21日に美濃国不破郡関ヶ原（岐阜県不破郡関ケ原町）で行われた野戦です。関ヶ原における決戦を中心に日本の全国各地で戦闘が行われ、関ヶ原の合戦・関ヶ原合戦とも呼ばれます。合戦当時は南北朝時代の古戦場・「青野原」や「青野カ原」と書かれた文献もある。主戦場となった関ヶ原古戦場跡は国指定の史跡となっています。豊臣秀吉が死んだ後の権力をめぐって石田三成が率いる西軍と、徳川家康が率いる東軍が戦いました。[徳川家康 - Wikipedia-2.pdf][石田三成 - Wikipedia-11.pdf]<<戦いの結果はどうなったのですか？>><<徳川家康と石田三成について教えてください>><<他にも有名な合戦がありますか？>>
###
"""
    # Query generation prompt
    query_prompt_template = """
以下は、過去の会話の履歴と、日本史に関するナレッジベースを検索して回答する必要のあるユーザーからの新しい質問です。
会話と新しい質問に基づいて、検索クエリを作成してください。
検索クエリには、引用されたファイルや文書の名前（例:info.txtやdoc.pdf）を含めないでください。
検索クエリには、括弧 []または<<>>内のテキストを含めないでください。
検索クエリを生成できない場合は、数字 0 だけを返してください。
"""
    query_prompt_few_shots = [
        {'role' : USER, 'content' : '徳川家康ってなにした人  ' },
        {'role' : ASSISTANT, 'content' : '徳川家康 人物 歴史' },
        {'role' : USER, 'content' : '徳川家康の武功を教えてください' },
        {'role' : ASSISTANT, 'content' : '徳川家康 人物 武功 業績' }
    ]

    def __init__(self, search_client: SearchClient, chatgpt_deployment: str, chatgpt_model: str, embedding_deployment: str, sourcepage_field: str, content_field: str):
        self.search_client = search_client
        self.chatgpt_deployment = chatgpt_deployment
        self.chatgpt_model = chatgpt_model
        self.embedding_deployment = embedding_deployment
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field
        self.chatgpt_token_limit = get_token_limit(chatgpt_model)

    async def run_until_final_call(self, history: list[dict[str, str]], overrides: dict[str, Any], should_stream: bool = False) -> tuple:
        has_text = overrides.get("retrieval_mode") in ["text", "hybrid", None]
        has_vector = overrides.get("retrieval_mode") in ["vectors", "hybrid", None]
        use_semantic_captions = True if overrides.get("semantic_captions") and has_text else False
        top = overrides.get("top") or 3
        exclude_category = overrides.get("exclude_category") or None
        filter = "category ne '{}'".format(exclude_category.replace("'", "''")) if exclude_category else None
        
        # ===================================================================================
        # STEP 1: チャット履歴と最後の質問に基づいて、GPTで最適化されたキーワード検索クエリを生成します。
        # ===================================================================================
        user_q = 'Generate search query for: ' + history[-1]["user"]
        messages = self.get_messages_from_history(
            self.query_prompt_template,
            self.chatgpt_model,
            history,
            user_q,
            self.query_prompt_few_shots,
            self.chatgpt_token_limit - len(user_q)
            )
        
        # ChatCompletion で検索クエリーを生成する
        chat_completion = await openai.ChatCompletion.acreate(
            deployment_id=self.chatgpt_deployment,
            model=self.chatgpt_model,
            messages=messages,
            temperature=0.0,
            max_tokens=100,
            n=1)

        query_text = chat_completion.choices[0].message.content
        if query_text.strip() == "0":
            query_text = history[-1]["user"] # より良いクエリを生成できなかった場合は、最後に入力されたクエリを使用する。

        # ================================================================================
        # STEP 2: GPT で生成したクエリを使用して、検索インデックスから関連するドキュメントを取得します。
        # ================================================================================
        # 検索モードにベクトルが含まれている場合は、クエリの埋め込みを計算します。
        if has_vector:
            query_vector = (await openai.Embedding.acreate(engine=self.embedding_deployment, input=query_text))["data"][0]["embedding"]
        else:
            query_vector = None

        # 検索モードがテキストを使用する場合は、テキストクエリのみを保持し、それ以外は削除します。
        if not has_text:
            query_text = None

        # 検索モードがテキストまたはハイブリッド（ベクトル＋テキスト）の場合、リクエストに応じてセマンティックリランカーを使用する。
        if overrides.get("semantic_ranker") and has_text:
            r = await self.search_client.search(query_text,
                                          filter=filter,
                                          query_type=QueryType.SEMANTIC,
                                          query_language="ja-jp",
                                          query_speller="none",
                                          semantic_configuration_name="default",
                                          top=top,
                                          query_caption="extractive|highlight-false" if use_semantic_captions else None,
                                          vector=query_vector,
                                          top_k=50 if query_vector else None,
                                          vector_fields="embedding" if query_vector else None)
        else:
            r = await self.search_client.search(query_text,
                                          filter=filter,
                                          top=top,
                                          vector=query_vector,
                                          top_k=50 if query_vector else None,
                                          vector_fields="embedding" if query_vector else None)
        if use_semantic_captions:
            results =[" SOURCE:" + doc[self.sourcepage_field] + ": " + nonewlines(" . ".join([c.text for c in doc['@search.captions']])) async for doc in r]
        else:
            results =[" SOURCE:" + doc[self.sourcepage_field] + ": " + nonewlines(doc[self.content_field]) async for doc in r]
        content = "\n".join(results) # 検索結果

        # =============================================================================
        # STEP 3: 検索結果とチャット履歴を使用して、文脈や内容に応じた回答を生成します。
        # =============================================================================
        
        follow_up_questions_prompt = self.follow_up_questions_prompt_content if overrides.get("suggest_followup_questions") else ""
        # プロンプトテンプレートを上書きする
        # クライアントがプロンプト全体を置き換えたり、接頭辞に >>> を使用して既存のプロンプトに注入したりできるようにする。
        prompt_override = overrides.get("prompt_template")
        if prompt_override is None:
            system_message = self.system_message_chat_conversation.format(injected_prompt="", follow_up_questions_prompt=follow_up_questions_prompt)
        elif prompt_override.startswith(">>>"):
            system_message = self.system_message_chat_conversation.format(injected_prompt=prompt_override[3:] + "\n", follow_up_questions_prompt=follow_up_questions_prompt)
        else:
            system_message = prompt_override.format(follow_up_questions_prompt=follow_up_questions_prompt)

        print(system_message) # 合成されたシステムプロンプトの確認用
        
        messages = self.get_messages_from_history(
            system_message,
            self.chatgpt_model,
            history,
            history[-1]["user"]+ "\n\n " + content, # モデルは長いシステムメッセージをうまく扱えない。フォローアップ質問のプロンプトを解決するために、最新のユーザー会話にソースを移動する。
            max_tokens=self.chatgpt_token_limit)
        msg_to_display = '\n\n'.join([str(message) for message in messages])

        extra_info = {"data_points": results, "thoughts": f"Searched for:<br>{query_text}<br><br>Conversations:<br>" + msg_to_display.replace('\n', '<br>')}
        
        # ChatCompletion で回答を生成する
        chat_coroutine = openai.ChatCompletion.acreate(
                deployment_id=self.chatgpt_deployment,
                model=self.chatgpt_model,
                messages=messages,
                temperature=overrides.get("temperature") or 0.0,
                max_tokens=1024,
                n=1,
                stream=should_stream)
        return (extra_info, chat_coroutine)

    async def run_without_streaming(self, history: list[dict[str, str]], overrides: dict[str, Any]) -> dict[str, Any]:
        extra_info, chat_coroutine = await self.run_until_final_call(history, overrides, should_stream=False)
        chat_content = (await chat_coroutine).choices[0].message.content
        extra_info["answer"] = chat_content
        return extra_info

    async def run_with_streaming(self, history: list[dict[str, str]], overrides: dict[str, Any]) -> AsyncGenerator[dict, None]:
        extra_info, chat_coroutine = await self.run_until_final_call(history, overrides, should_stream=True)
        yield extra_info
        async for event in await chat_coroutine:
            yield event

    def get_messages_from_history(self, system_prompt: str, model_id: str, history: list[dict[str, str]], user_conv: str, few_shots = [], max_tokens: int = 4096) -> list:
        message_builder = MessageBuilder(system_prompt, model_id)

        # どのような応答が欲しいかをチャットに示す例を追加してください。チャットはどのような応答でも模倣しようとし、システムメッセージに示されたルールに一致することを確認します。
        for shot in few_shots:
            message_builder.append_message(shot.get('role'), shot.get('content'))

        user_content = user_conv
        append_index = len(few_shots) + 1

        message_builder.append_message(self.USER, user_content, index=append_index)

        for h in reversed(history[:-1]):
            if bot_msg := h.get("bot"):
                message_builder.append_message(self.ASSISTANT, bot_msg, index=append_index)
            if user_msg := h.get("user"):
                message_builder.append_message(self.USER, user_msg, index=append_index)
            if message_builder.token_length > max_tokens:
                break

        messages = message_builder.messages
        return messages
