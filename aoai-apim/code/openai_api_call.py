from flask import Flask, redirect, url_for, session, request, jsonify
from authlib.integrations.flask_client import OAuth
from functools import partial
import argparse
import os
import json
import requests

def create_app(tenant_id, client_id, client_secret, redirect_uri, scope, apim_name, subscription_key):
    app = Flask(__name__)
    app.secret_key = 'random_secret'
    oauth = OAuth(app)

    azure = oauth.register(
        'azure',
        client_id=client_id,
        client_secret=client_secret,
        authorize_url='https://login.microsoftonline.com/' + tenant_id + '/oauth2/v2.0/authorize',
        authorize_params=None,
        access_token_url='https://login.microsoftonline.com/' + tenant_id + '/oauth2/v2.0/token',
        access_token_params=None,
        refresh_token_url=None,
        redirect_uri=redirect_uri,
        client_kwargs={'scope': scope}
    )

    @app.route('/')
    def login():
        return azure.authorize_redirect(url_for('callback', _external=True))

    @app.route('/callback')
    def callback():
        token = azure.authorize_access_token()
        session['token'] = token['access_token']
        return redirect(url_for('me'))

    @app.route('/me')
    def me():
        token = session.get('token')
        headers = {
            'Authorization': 'Bearer ' + token,
            'Ocp-Apim-Subscription-Key': subscription_key,
            'Content-Type': 'application/json'
        }

        data = {
            "model": "gpt-35-turbo",
            "messages": [{
                "role": "user",
                "content": "こんにちは！"
            }]
        }

        response = requests.post("https://" + apim_name + ".azure-api.net/api/deployments/chatgpt/chat/completions?api-version=2023-07-01-preview"
                                , headers=headers, json=data)
        return jsonify(response.json())

    return app

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Azure API Managementで発行したAzure OpenAI APIを呼び出すFlaskアプリケーション")
    parser.add_argument("--tenant_id", required=True)
    parser.add_argument("--client_id", required=True)
    parser.add_argument("--client_secret", required=True)
    parser.add_argument("--redirect_uri", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--apim_name", required=True)
    parser.add_argument("--subscription_key", required=True)

    args = parser.parse_args()

    app = create_app(args.tenant_id, args.client_id, args.client_secret, args.redirect_uri, args.scope, args.apim_name, args.subscription_key)
    app.run()
