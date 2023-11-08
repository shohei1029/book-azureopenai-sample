import io
import json
import logging
import mimetypes
import os
import time
from typing import AsyncGenerator

import aiohttp
import openai

#Cosmos DB
from azure.identity.aio import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.search.documents.aio import SearchClient
from azure.storage.blob.aio import BlobServiceClient
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from quart import (
    Blueprint,
    Quart,
    abort,
    current_app,
    jsonify,
    make_response,
    request,
    send_file,
    send_from_directory,
)

from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
from approaches.readpluginsretrieve import ReadPluginsRetrieve
from approaches.readretrieveread import ReadRetrieveReadApproach
from approaches.retrievethenread import RetrieveThenReadApproach

# Replace these with your own values, either in environment variables or directly here
AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "mystorageaccount")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER", "content")
AZURE_SEARCH_SERVICE = os.getenv("AZURE_SEARCH_SERVICE", "gptkb")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "gptkbindex")
AZURE_OPENAI_SERVICE = os.getenv("AZURE_OPENAI_SERVICE", "myopenai")
AZURE_OPENAI_CHATGPT_MODEL = os.getenv("AZURE_OPENAI_CHATGPT_MODEL", "gpt-35-turbo-16k")
AZURE_OPENAI_GPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT", "davinci")
AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT", "chat16k")
AZURE_OPENAI_EMB_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT", "embedding")

KB_FIELDS_CONTENT = os.getenv("KB_FIELDS_CONTENT", "content")
KB_FIELDS_CATEGORY = os.getenv("KB_FIELDS_CATEGORY", "category")
KB_FIELDS_SOURCEPAGE = os.getenv("KB_FIELDS_SOURCEPAGE", "sourcepage")

CONFIG_OPENAI_TOKEN = "openai_token"
CONFIG_CREDENTIAL = "azure_credential"
CONFIG_ASK_APPROACHES = "ask_approaches"
CONFIG_CHAT_APPROACHES = "chat_approaches"
CONFIG_BLOB_CLIENT = "blob_client"

APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

bp = Blueprint("routes", __name__, static_folder='static')

@bp.route("/")
async def index():
    return await bp.send_static_file("index.html")

@bp.route("/favicon.ico")
async def favicon():
    return await bp.send_static_file("favicon.ico")

@bp.route("/assets/<path:path>")
async def assets(path):
    return await send_from_directory("static/assets", path)

# Serve content files from blob storage from within the app to keep the example self-contained.
# *** NOTE *** this assumes that the content files are public, or at least that all users of the app
# can access all the files. This is also slow and memory hungry.

# この例を自己完結的なものにするために、アプリ内からblobストレージにコンテンツファイルを配信する。
# *** NOTE *** この例では、コンテンツファイルが公開されているか、少なくともアプリの全ユーザーが
# すべてのファイルにアクセスできることを前提としています。また, これは低速でメモリを消費します.
@bp.route("/content/<path>")
async def content_file(path):
    logging.info("content_file: " + path)
    blob_container = current_app.config[CONFIG_BLOB_CLIENT].get_container_client(AZURE_STORAGE_CONTAINER)
    logging.info("blob_container: " + blob_container.get_blob_client(path).url)
    blob = await blob_container.get_blob_client(path).download_blob()
    if not blob.properties or not blob.properties.has_key("content_settings"):
        abort(404)
    mime_type = blob.properties["content_settings"]["content_type"]
    if mime_type == "application/octet-stream":
        mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    blob_file = io.BytesIO()
    await blob.readinto(blob_file)
    blob_file.seek(0)
    return await send_file(blob_file, mimetype=mime_type, as_attachment=False, attachment_filename=path)

@bp.route("/ask", methods=["POST"])
async def ask():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415
    request_json = await request.get_json()
    approach = request_json["approach"]
    try:
        impl = current_app.config[CONFIG_ASK_APPROACHES].get(approach)
        if not impl:
            return jsonify({"error": "unknown approach"}), 400
        #plugin の場合、非同期だと失敗するので同期で実行
        if approach == "rpr":
            r = impl.run(request_json["question"], request_json.get("overrides") or {})
            logging.info("ReadPluginsRetrieve is completed.")
        else:
            r = await impl.run(request_json["question"], request_json.get("overrides") or {})
        return jsonify(r)
    except Exception as e:
        logging.exception("Exception in /ask")
        return jsonify({"error": str(e)}), 500

@bp.route("/chat", methods=["POST"])
async def chat():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415
    request_json = await request.get_json()
    approach = request_json["approach"]
    try:
        impl = current_app.config[CONFIG_CHAT_APPROACHES].get(approach)
        if not impl:
            return jsonify({"error": "unknown approach"}), 400
        # Workaround for: https://github.com/openai/openai-python/issues/371
        async with aiohttp.ClientSession() as s:
            openai.aiosession.set(s)
            r = await impl.run_without_streaming(request_json["history"], request_json.get("overrides", {}))
        return jsonify(r)
    except Exception as e:
        logging.exception("Exception in /chat")
        return jsonify({"error": str(e)}), 500


async def format_as_ndjson(r: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    async for event in r:
        yield json.dumps(event, ensure_ascii=False) + "\n"

@bp.route("/chat_stream", methods=["POST"])
async def chat_stream():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415
    request_json = await request.get_json()
    approach = request_json["approach"]
    try:
        impl = current_app.config[CONFIG_CHAT_APPROACHES].get(approach)
        if not impl:
            return jsonify({"error": "unknown approach"}), 400
        response_generator = impl.run_with_streaming(request_json["history"], request_json.get("overrides", {}))
        response = await make_response(format_as_ndjson(response_generator))
        response.timeout = None # type: ignore
        return response
    except Exception as e:
        logging.exception("Exception in /chat")
        return jsonify({"error": str(e)}), 500


@bp.before_request
async def ensure_openai_token():
    openai_token = current_app.config[CONFIG_OPENAI_TOKEN]
    if openai_token.expires_on < time.time() + 60:
        openai_token = await current_app.config[CONFIG_CREDENTIAL].get_token("https://cognitiveservices.azure.com/.default")
        current_app.config[CONFIG_OPENAI_TOKEN] = openai_token
        openai.api_key = openai_token.token

@bp.before_app_serving
async def setup_clients():

    # Use the current user identity to authenticate with Azure OpenAI, Cognitive Search and Blob Storage (no secrets needed,
    # just use 'az login' locally, and managed identity when deployed on Azure). If you need to use keys, use separate AzureKeyCredential instances with the
    # keys for each service
    # If you encounter a blocking error during a DefaultAzureCredential resolution, you can exclude the problematic credential by using a parameter (ex. exclude_shared_token_cache_credential=True)

    # Azure OpenAI、Cognitive Search、Blob Storageでの認証には、現在のユーザーIDを使用します（シークレットは必要ありません、
    # ローカルでは 'az login' を使用し、Azure 上にデプロイされている場合はマネージド ID を使用するだけです)。キーを使用する必要がある場合は、各サービスのキーを持つ個別の AzureKeyCredential インスタンスを使用します。
    # DefaultAzureCredentialの解決中にブロックエラーが発生した場合、パラメータを使用することで問題のあるクレデンシャルを除外することができます(ex.exclude_shared_token_cache_credential=True)
    azure_credential = DefaultAzureCredential(exclude_shared_token_cache_credential = True)
    # Set up clients for Cognitive Search and Storage
    search_client = SearchClient(
        endpoint=f"https://{AZURE_SEARCH_SERVICE}.search.windows.net",
        index_name=AZURE_SEARCH_INDEX,
        credential=azure_credential)
    blob_client = BlobServiceClient(
        account_url=f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net",
        credential=azure_credential)

    # Set up a Cosmos DB client to store the chat history
    # endpoint = 'https://<Your-CosmosDB-Account>.documents.azure.com:443/'
    # key = '<Your-CosmosDB-Key>'
    # cosmos_container = []
    # try:
    #     cosmos_client = CosmosClient(url=endpoint, credential=key)
    #     database = cosmos_client.create_database_if_not_exists(id="ChatGPT")
    #     partitionKeyPath = PartitionKey(path="/id")
    #     cosmos_container = database.create_container_if_not_exists(
    #         id="ChatLogs", partition_key=partitionKeyPath
    #     )
    # except Exception as e:
    #     logging.exception(e)
    #     pass

    # Used by the OpenAI SDK
    openai.api_base = f"https://{AZURE_OPENAI_SERVICE}.openai.azure.com"
    openai.api_version = "2023-07-01-preview"
    openai.api_type = "azure_ad"
    openai_token = await azure_credential.get_token(
        "https://cognitiveservices.azure.com/.default"
    )
    openai.api_key = openai_token.token

    # Store on app.config for later use inside requests
    current_app.config[CONFIG_OPENAI_TOKEN] = openai_token
    current_app.config[CONFIG_CREDENTIAL] = azure_credential
    current_app.config[CONFIG_BLOB_CLIENT] = blob_client
    # Various approaches to integrate GPT and external knowledge, most applications will use a single one of these patterns
    # or some derivative, here we include several for exploration purposes
    # GPTと外部の知識を統合するための様々なアプローチ。ほとんどのアプリケーションは、これらのパターンのうちの1つ、あるいは派生したものを使うでしょう。
    # このサンプルでは ReadDecomposeAsk 機能は ChatGPT プラグイン機能に代替しました。
    current_app.config[CONFIG_ASK_APPROACHES] = {
        "rtr": RetrieveThenReadApproach(
            search_client,
            AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            AZURE_OPENAI_CHATGPT_MODEL,
            AZURE_OPENAI_EMB_DEPLOYMENT,
            KB_FIELDS_SOURCEPAGE,
            KB_FIELDS_CONTENT
        ),
        "rrr": ReadRetrieveReadApproach(
            search_client,
            AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            AZURE_OPENAI_EMB_DEPLOYMENT,
            KB_FIELDS_SOURCEPAGE,
            KB_FIELDS_CONTENT
        ),
        "rpr": ReadPluginsRetrieve(
            AZURE_OPENAI_CHATGPT_DEPLOYMENT
        )
    }
    current_app.config[CONFIG_CHAT_APPROACHES] = {
        "rrr": ChatReadRetrieveReadApproach(
            search_client,
            AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            AZURE_OPENAI_CHATGPT_MODEL,
            AZURE_OPENAI_EMB_DEPLOYMENT,
            KB_FIELDS_SOURCEPAGE,
            KB_FIELDS_CONTENT,
        )
        # "rrr": ChatReadRetrieveReadApproachCosmosDB (
        #     search_client,
        #     cosmos_container,
        #     AZURE_OPENAI_CHATGPT_DEPLOYMENT,
        #     AZURE_OPENAI_CHATGPT_MODEL,
        #     AZURE_OPENAI_EMB_DEPLOYMENT,
        #     KB_FIELDS_SOURCEPAGE,
        #     KB_FIELDS_CONTENT,
        # )
    }


def create_app():
    if APPLICATIONINSIGHTS_CONNECTION_STRING:
        configure_azure_monitor()
        AioHttpClientInstrumentor().instrument()
    app = Quart(__name__)
    app.register_blueprint(bp)
    app.asgi_app = OpenTelemetryMiddleware(app.asgi_app)

    return app
