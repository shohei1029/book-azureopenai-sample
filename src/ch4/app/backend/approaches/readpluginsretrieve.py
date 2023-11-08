import logging
from typing import Any

import openai
from langchain.agents import AgentType, initialize_agent, load_tools
from langchain.agents.mrkl import prompt
from langchain.callbacks.manager import CallbackManager
from langchain.chat_models import AzureChatOpenAI
from langchain.tools import AIPluginTool

from approaches.approach import AskApproach
from langchainadapters import HtmlCallbackHandler
from requests.exceptions import ConnectionError

class ReadPluginsRetrieve(AskApproach):
    def __init__(self, openai_deployment: str):
        self.openai_deployment = openai_deployment

    def run(self, q: str, overrides: dict[str, Any]) -> Any:
        try:
            cb_handler = HtmlCallbackHandler()
            cb_manager = CallbackManager(handlers=[cb_handler])

            #llm = ChatOpenAI(model_name="gpt-4-0613", temperature=0)
            llm = AzureChatOpenAI(deployment_name=self.openai_deployment,
                                temperature=0.0,
                                openai_api_base=openai.api_base,
                                openai_api_version=openai.api_version,
                                openai_api_type=openai.api_type,
                                openai_api_key=openai.api_key)
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
                                        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                                        #agent=AgentType.OPENAI_FUNCTIONS,
                                        verbose=True,
                                        agent_kwargs=dict(suffix=SUFFIX + prompt.SUFFIX),
                                        handle_parsing_errors=True,
                                        callback_manager = cb_manager,
                                        max_iterations=5,
                                        early_stopping_method="generate")

            result = agent_chain.run(q)
        except ConnectionError as e:
            logging.exception(e)
            result = "すみません、わかりません。(ConnectionError)"
        except Exception as e:
            logging.exception(e)
            result = "すみません、わかりません。(Error)"

        return {"data_points":  [], "answer": result, "thoughts": cb_handler.get_and_reset_log()}
