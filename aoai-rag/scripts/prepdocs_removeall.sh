#!/bin/sh

set -eu
# -e 何かしらのコマンドがexit code 0 以外を出力した際に即座にerror exit
# -u 未定義の変数の利用があればエラーメッセージを出力してerror exit
# -x 実行ログを出力する

echo ""
echo "Loading azd .env file from current environment"
echo ""

while IFS='=' read -r key value; do
    value=$(echo "$value" | sed 's/^"//' | sed 's/"$//')
    export "$key=$value"
done <<EOF
$(azd env get-values)
EOF

echo 'Creating python virtual environment "scripts/.venv"'
python3 -m venv scripts/.venv

echo 'Installing dependencies from "requirements.txt" into virtual environment'
./scripts/.venv/bin/python -m pip install -r scripts/requirements.txt

echo 'Running "prepdocs.py"'
./scripts/.venv/bin/python ./scripts/prepdocs.py './data/*' --storageaccount "$AZURE_STORAGE_ACCOUNT" --container "$AZURE_STORAGE_CONTAINER" --searchservice "$AZURE_SEARCH_SERVICE" --openaiservice "$AZURE_OPENAI_SERVICE" --openaideployment "$AZURE_OPENAI_EMB_DEPLOYMENT" --index "$AZURE_SEARCH_INDEX" --formrecognizerservice "$AZURE_FORMRECOGNIZER_SERVICE" --tenantid "$AZURE_TENANT_ID" --openaimodelname "$AZURE_OPENAI_EMB_MODEL_NAME" --removeall -v
