import csv
import logging
from typing import Any, Callable
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import (
    QueryType,
    VectorizedQuery
)
from openai import AsyncOpenAI
from langchain.agents import (
    AgentType,
    Tool,
    initialize_agent,
)
from langchain.agents.mrkl import prompt
from langchain.callbacks.manager import CallbackManager
from langchain.chat_models import AzureChatOpenAI
from langchain.tools import BaseTool

from approaches.approach import AskApproach
from langchainadapters import HtmlCallbackHandler
from text import nonewlines

class ReadRetrieveReadApproach(AskApproach):
    """
    質問に対して、どのような情報が欠けているのかを確認するために、質問を繰り返し評価し、すべての情報が揃ったところで、回答を作成することを試みる。
    各反復は 2 つの部分で構成されています。
     1. GPT を使用して、さらに情報が必要かどうかを確認する。
     2.より多くのデータが必要な場合は、要求された「ツール」を使ってデータを取得する。
    GPT への最後の呼び出しが、実際の質問に答える。
    これは、MRKL の論文[1]にインスパイアされ、Langchain の実装を使ってここで適用されている。

    [1] E. Karpas, et al. arXiv:2205.00445
    """

    def __init__(self, search_client: SearchClient, openai_client: AsyncOpenAI, openai_api_version: str, openai_endpoint: str, openai_ad_token: Callable[[], str], openai_deployment: str, embedding_deployment: str, sourcepage_field: str, content_field: str):
        self.search_client = search_client
        self.openai_client = openai_client
        self.openai_api_version = openai_api_version
        self.openai_endpoint = openai_endpoint
        self.openai_ad_token = openai_ad_token
        self.openai_deployment = openai_deployment
        self.embedding_deployment = embedding_deployment
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field

    async def retrieve(self, query_text: str, overrides: dict[str, Any]) -> Any:
        has_text = overrides.get("retrieval_mode") in ["text", "hybrid", None]
        has_vector = overrides.get("retrieval_mode") in ["vectors", "hybrid", None]
        use_semantic_captions = True if overrides.get("semantic_captions") and has_text else False
        top = overrides.get("top") or 3
        exclude_category = overrides.get("exclude_category") or None
        filter = "category ne '{}'".format(exclude_category.replace("'", "''")) if exclude_category else None
        # If retrieval mode includes vectors, compute an embedding for the query
        if has_vector:
            embedding = await self.openai_client.embeddings.create(
                model=self.embedding_deployment,
                input=query_text
            )
            query_vector = embedding.data[0].embedding
        else:
            query_vector = None

        # Only keep the text query if the retrieval mode uses text, otherwise drop it
        if not has_text:
            query_text = ""

        # Use semantic ranker if requested and if retrieval mode is text or hybrid (vectors + text)
        if overrides.get("semantic_ranker") and has_text:
            r = await self.search_client.search(search_text=query_text,
                                          filter=filter,
                                          query_type=QueryType.SEMANTIC,
                                          semantic_configuration_name="default",
                                          top = top,
                                          query_caption="extractive|highlight-false" if use_semantic_captions else None,
                                          vector_queries=[VectorizedQuery(vector=query_vector, k_nearest_neighbors=top, fields="embedding")] if query_vector else None)
        else:
            r = await self.search_client.search(search_text=query_text,
                                          filter=filter,
                                          top=top,
                                          vector_queries=[VectorizedQuery(vector=query_vector, k_nearest_neighbors=top, fields="embedding")] if query_vector else None)
        if use_semantic_captions:
            results = [doc[self.sourcepage_field] + ":" + nonewlines(" -.- ".join([c.text for c in doc['@search.captions']])) for doc in r]
        else:
            results = [doc[self.sourcepage_field] + ":" + nonewlines(doc[self.content_field]) async for doc in r]
        content = "\n".join(results)
        return results, content

    async def run(self, q: str, overrides: dict[str, Any]) -> dict[str, Any]:

        retrieve_results = None
        async def retrieve_and_store(q: str) -> Any:
            nonlocal retrieve_results
            retrieve_results, content = await self.retrieve(q, overrides)
            return content

        # Use to capture thought process during iterations
        cb_handler = HtmlCallbackHandler()
        cb_manager = CallbackManager(handlers=[cb_handler])

        # Tool dataclass 法と Subclassing the BaseTool class 法の異なる記法を示しています
        tools = [
            Tool(name="PeopleSearchTool",
                func=retrieve_and_store,
                coroutine=retrieve_and_store,
                description="日本の歴史の人物情報の検索に便利です。ユーザーの質問から検索クエリーを生成して検索します。クエリーは文字列のみを受け付けます"
                ),
            CafeSearchTool()
        ]

       #llm = ChatOpenAI(model_name="gpt-4-0613", temperature=0)
        llm = AzureChatOpenAI(azure_deployment=self.openai_deployment,
                              api_version=self.openai_api_version,
                              azure_endpoint=self.openai_endpoint,
                              azure_ad_token_provider=self.openai_ad_token,
                              temperature=overrides.get("temperature") or 0.3,
                              )
        SUFFIX = """
        Answer should be in Japanese.
        """
        agent_chain = initialize_agent(tools,
                                    llm,
                                    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                                    #agent=AgentType.OPENAI_FUNCTIONS,
                                    verbose=True,
                                    agent_kwargs=dict(suffix=SUFFIX + prompt.SUFFIX),
                                    callback_manager = cb_manager,
                                    handle_parsing_errors=True,
                                    max_iterations=5,
                                    early_stopping_method="generate")
        #最大反復回数を制限する max_iterations, early_stopping_method
        #https://python.langchain.com/docs/modules/agents/how_to/max_iterations
        #解析エラーを処理する handle_parsing_errors
        #https://python.langchain.com/docs/modules/agents/how_to/handle_parsing_errors

        result = await agent_chain.arun(q)
        # Remove references to tool names that might be confused with a citation
        #result = result.replace("[CognitiveSearch]", "").replace("[Employee]", "")
        return {"data_points": retrieve_results or [], "answer": result, "thoughts": cb_handler.get_and_reset_log()}

# 検索を行うカスタムツールを定義。CSV からルックアップを行う例です。
# Subclassing the BaseTool class
# https://python.langchain.com/docs/modules/agents/tools/custom_tools
class CafeSearchTool(BaseTool):
    data: dict[str, str] = {}
    name = "CafeSearchTool"
    description = "武将のゆかりのカフェを検索するのに便利です。カフェの検索クエリには、武将の**名前のみ**を入力してください。"

    # Use the tool synchronously.
    def _run(self, query: str) -> str:
        """Use the tool."""
        return query

    # Use the tool asynchronously.
    async def _arun(self, query: str) -> str:
        filename = "data/restaurantinfo.csv"
        key_field = "name"
        try:
            with open(filename, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    self.data[row[key_field]] =  "\n".join([f"{i}:{row[i]}" for i in row])

        except Exception as e:
            logging.exception("File read error:", e)

        return self.data.get(query, "")