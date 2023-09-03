import json

import quart
import quart_cors
from quart import request
app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")

# Keep track of reviews. Does not persist if Python session is restarted.
_REVIEWS = {}

@app.get("/reviews/<string:username>")
async def get_reviews(username):
    _REVIEWS["hanachan"] = "review: 5 stars"
    return quart.Response(response=json.dumps(_REVIEWS.get(username, [])), status=200)

@app.get("/search")
async def search():

    query = request.args.get("q")
    print(query)
    list_rest = [{"bushoname": "源範頼", "cafename": "カフェかば殿", "rating": 4.1, "area": "修善寺"},
                {"bushoname": "源頼朝", "cafename": "源氏庵", "rating": 3.6, "area": "鎌倉"},
                {"bushoname": "源実朝", "cafename": "カフェ十三人", "rating": 3.5, "area": "修善寺"}]

    list_search = list(filter(lambda item : item['bushoname'] == query, list_rest))
    dict_search = {}
    if len(list_search) > 0:
        dict_search = list_search[0]
    return quart.Response(response=json.dumps(dict_search, ensure_ascii=False), status=200)


@app.get("/logo.png")
async def plugin_logo():
    filename = 'logo.png'
    return await quart.send_file(filename, mimetype='image/png')

@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open("./.well-known/ai-plugin.json") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/json")

@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open("openapi.yaml") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/yaml")

def main():
    app.run(debug=True, host="0.0.0.0", port=5005)

if __name__ == "__main__":
    main()
