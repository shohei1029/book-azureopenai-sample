from typing import Any, Optional, Sequence

import openai
import langchain
from approaches.approach import AskApproach
from langchainadapters import HtmlCallbackHandler
from langchain.callbacks.manager import CallbackManager, Callbacks
from text import nonewlines
from langchain.chat_models import ChatOpenAI
from langchain.chat_models import AzureChatOpenAI
from langchain.agents import load_tools, initialize_agent
from langchain.agents import AgentType
from langchain.tools import AIPluginTool
from langchain.agents.mrkl import prompt
from langchain.schema import SystemMessage

class ReadPluginsRetrieve(AskApproach):
    def __init__(self, openai_deployment: str):
        self.openai_deployment = openai_deployment

    def run(self, q: str, overrides: dict[str, Any]) -> Any:

        cb_handler = HtmlCallbackHandler()
        cb_manager = CallbackManager(handlers=[cb_handler])

        #llm = ChatOpenAI(model_name="gpt-4-0613", temperature=0)
        llm = AzureChatOpenAI(deployment_name=self.openai_deployment, temperature=0.0,
                              openai_api_base=openai.api_base, openai_api_version=openai.api_version, 
                              openai_api_type=openai.api_type, openai_api_key=openai.api_key)
        tools = load_tools(["requests_all"])
        plugin_urls = ["http://localhost:5005/.well-known/ai-plugin.json", "http://localhost:5006/.well-known/ai-plugin.json"]

        tools += [AIPluginTool.from_plugin_url(url) for url in plugin_urls]

        SUFFIX = """
        Answer should be in Japanese. Use http instead of https for endpoint.
        If there is no year in the reservation, use the year 2023. 
        """

        # Responsible AI MetaPrompt
        #**IMPORTANT**
        #If a restaurant reservation is available, must check with the user before making a reservation if yes.'
        agent_chain = initialize_agent(tools,
                                    llm,
                                    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True,
                                    agent_kwargs=dict(suffix=SUFFIX + prompt.SUFFIX),
                                    handle_parsing_errors=True,
                                    callback_manager = cb_manager,
                                    max_iterations=5,
                                    early_stopping_method="generate")
        try:
            result = agent_chain.run(q)
        except Exception as e:
            print(e)
            result = "すみません、わかりません。"

        return {"data_points":  [], "answer": result, "thoughts": cb_handler.get_and_reset_log()}
