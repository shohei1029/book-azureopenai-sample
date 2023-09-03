import json

import quart
import quart_cors
from quart import request
import openai

app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")

# こっちで変換するのもありかも
def get_isodatetime(strdatetime):
    prompt = """以下の日時を ISO 8601 に変換しなさい。年が無い場合は、2023年を使いなさい。
    Datetime: {}
    """
    res = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt.format(strdatetime),
        max_tokens=2048,
        temperature=0
    )
    return(res.choices[0].text)

# Keep track of todo's. Does not persist if Python session is restarted.
_TODOS = {}
   
@app.post("/reserve")
async def reserve_restaurant():
    request = await quart.request.get_json(force=True)
    print(request)
    datetime = request['datetime']
    print(get_isodatetime(datetime))

    return quart.Response(response='OK', status=200)

@app.get("/search")
async def search():

    query = request.args.get("q")
    datetime = request.args.get("datetime")
    print(query, datetime)
    print(get_isodatetime(datetime))
    list_rest = [{"cafename": "カフェかば殿", "2023/07/01 18:00-19:00": "空き"}]

    list_search = list(filter(lambda item : item['cafename'] == query, list_rest))
    dict_search = {"Cafe not found"}
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
    app.run(debug=True, host="0.0.0.0", port=5006)

if __name__ == "__main__":
    main()
