import os, flask
from openai import AzureOpenAI
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

client = AzureOpenAI(
  azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
  api_key=os.getenv("AZURE_OPENAI_KEY"),  
  api_version=os.getenv("AZURE_OPENAI_VERSION")
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat():
    prompt = request.args.get("prompt")
    response = client.chat.completions.create(
        model=os.getenv("AZURE_DEPLOYMENT_ID"),
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        stream=True
    )

    def stream():
        for chunk in response:
            finish_reason = chunk.choices[0].finish_reason
            if finish_reason == 'stop':
                yield 'data: %s\n\n' % '[DONE]'
            else:
                delta = chunk.choices[0].delta.content or ""
                yield 'data: %s\n\n' % delta.replace('\n', '[NEWLINE]')
    return flask.Response(stream(), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run()
