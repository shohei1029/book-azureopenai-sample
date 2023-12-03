from typing import Any

import openai
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import QueryType

from approaches.approach import AskApproach
from core.messagebuilder import MessageBuilder
from text import nonewlines


class RetrieveThenReadApproach(AskApproach):
    """
    Simple retrieve-then-read implementation, using the Cognitive Search and OpenAI APIs directly. It first retrieves
    top documents from search, then constructs a prompt with them, and then uses OpenAI to generate an completion
    (answer) with that prompt.
    Cognitive Search と Azure OpenAI の API を直接使用した、シンプルな retrieve-then-read の実装です。
    まず検索から上位のドキュメントを取得し、それを使ってプロンプトを作成し、OpenAI を使ってそのプロンプトを使った補完（回答）を生成します。
    """

    system_chat_template = \
"あなたは日本の歴史に関する質問をサポートする教師アシスタントです。" + \
"質問者が「私」で質問しても、「あなた」を使って質問者を指すようにする。" + \
"次の質問に、以下の出典で提供されたデータのみを使用して答えてください。" + \
"表形式の情報については、htmlテーブルとして返してください。マークダウン形式で返さないでください。" + \
"各出典元には、名前の後にコロンと実際の情報があり、回答で使用する各事実には必ず出典名を記載します。" + \
"以下の出典の中から答えられない場合は、「わかりません」と答えてください。" 
    #shots/sample conversation
    question = """
'Question: '源頼朝の具体的な功績を教えてください'

Sources:
info1.txt: 「本領安堵」「新恩給付」という豪族たちの最大の願望を実現し、坂東豪族の支持を集めた。
info2.pdf: 1185年に設置されたこの守護地頭は源頼朝の代表的な政治政策です。
info3.pdf: 源頼朝は、御家人の所領の保証、敵方の没収所領の給付を行いました。
info4.pdf: 平氏追討を名目にした軍事的支配権の行使を通じて、鎌倉政権を確立しました。
"""
    answer = "源頼朝は、御家人の所領の保証、敵方の没収所領の給付を行い、「本領安堵」「新恩給付」という豪族たちの最大の願望を実現し、坂東豪族の支持を集めた。[info1.txt][info3.pdf]  また、平氏追討を名目にした軍事的支配権の行使を通じて、鎌倉政権を確立し、[info4.txt] 守護地頭という重要な政策を確立しました。[info2.txt]"

    def __init__(self, search_client: SearchClient, openai_deployment: str, chatgpt_model: str, embedding_deployment: str, sourcepage_field: str, content_field: str):
        self.search_client = search_client
        self.openai_deployment = openai_deployment
        self.chatgpt_model = chatgpt_model
        self.embedding_deployment = embedding_deployment
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field

    async def run(self, q: str, overrides: dict[str, Any]) -> dict[str, Any]:
        has_text = overrides.get("retrieval_mode") in ["text", "hybrid", None]
        has_vector = overrides.get("retrieval_mode") in ["vectors", "hybrid", None]
        use_semantic_captions = True if overrides.get("semantic_captions") and has_text else False
        top = overrides.get("top") or 3
        exclude_category = overrides.get("exclude_category") or None
        filter = "category ne '{}'".format(exclude_category.replace("'", "''")) if exclude_category else None

        # If retrieval mode includes vectors, compute an embedding for the query
        if has_vector:
            query_vector = (await openai.Embedding.acreate(engine=self.embedding_deployment, input=q))["data"][0]["embedding"]
        else:
            query_vector = None

        # Only keep the text query if the retrieval mode uses text, otherwise drop it
        query_text = q if has_text else ""

        # Use semantic ranker if requested and if retrieval mode is text or hybrid (vectors + text)
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
            results = [doc[self.sourcepage_field] + ": " + nonewlines(" . ".join([c.text for c in doc['@search.captions']])) async for doc in r]
        else:
            results = [doc[self.sourcepage_field] + ": " + nonewlines(doc[self.content_field]) async for doc in r]
        content = "\n".join(results)

        message_builder = MessageBuilder(overrides.get("prompt_template") or self.system_chat_template, self.chatgpt_model)

        # add user question
        user_content = q + "\n" + f"Sources:\n {content}"
        message_builder.append_message('user', user_content)

        # Add shots/samples. This helps model to mimic response and make sure they match rules laid out in system message.
        message_builder.append_message('assistant', self.answer)
        message_builder.append_message('user', self.question)

        messages = message_builder.messages
        chat_completion = await openai.ChatCompletion.acreate(
            deployment_id=self.openai_deployment,
            model=self.chatgpt_model,
            messages=messages,
            temperature=overrides.get("temperature") or 0.3,
            max_tokens=1024,
            n=1)

        return {"data_points": results, "answer": chat_completion.choices[0].message.content, "thoughts": f"Question:<br>{query_text}<br><br>Prompt:<br>" + '\n\n'.join([str(message) for message in messages])}
