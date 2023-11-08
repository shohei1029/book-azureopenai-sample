#!/bin/sh

if [ "$CODESPACES" = "true" ]; then
    azd auth login --client-id $(echo $AZURE_CREDENTIALS | jq -r .clientId) --client-secret $(echo $AZURE_CREDENTIALS | jq -r .clientSecret) --tenant-id $AZURE_TENANT_ID
    azd env set AZURE_ENV_NAME $AZURE_ENV_NAME  --no-prompt
    azd env set AZD_PIPELINE_PROVIDER $AZD_PIPELINE_PROVIDER  --no-prompt
    azd env set AZURE_FORMRECOGNIZER_RESOURCE_GROUP $AZURE_FORMRECOGNIZER_RESOURCE_GROUP  --no-prompt
    azd env set AZURE_FORMRECOGNIZER_SERVICE $AZURE_FORMRECOGNIZER_SERVICE  --no-prompt
    azd env set AZURE_LOCATION $AZURE_LOCATION  --no-prompt
    azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT $AZURE_OPENAI_CHATGPT_DEPLOYMENT  --no-prompt
    azd env set AZURE_OPENAI_CHATGPT_MODEL $AZURE_OPENAI_CHATGPT_MODEL  --no-prompt
    azd env set AZURE_OPENAI_EMB_DEPLOYMENT $AZURE_OPENAI_EMB_DEPLOYMENT  --no-prompt
    azd env set AZURE_OPENAI_EMB_MODEL_NAME $AZURE_OPENAI_EMB_MODEL_NAME  --no-prompt
    azd env set AZURE_OPENAI_RESOURCE_GROUP $AZURE_OPENAI_RESOURCE_GROUP  --no-prompt
    azd env set AZURE_OPENAI_SERVICE $AZURE_OPENAI_SERVICE  --no-prompt
    azd env set AZURE_RESOURCE_GROUP $AZURE_RESOURCE_GROUP  --no-prompt
    azd env set AZURE_SEARCH_INDEX $AZURE_SEARCH_INDEX  --no-prompt
    azd env set AZURE_SEARCH_SERVICE $AZURE_SEARCH_SERVICE  --no-prompt
    azd env set AZURE_SEARCH_SERVICE_RESOURCE_GROUP $AZURE_SEARCH_SERVICE_RESOURCE_GROUP  --no-prompt
    azd env set AZURE_STORAGE_ACCOUNT $AZURE_STORAGE_ACCOUNT  --no-prompt
    azd env set AZURE_STORAGE_CONTAINER $AZURE_STORAGE_CONTAINER  --no-prompt
    azd env set AZURE_STORAGE_RESOURCE_GROUP $AZURE_STORAGE_RESOURCE_GROUP  --no-prompt
    azd env set AZURE_SUBSCRIPTION_ID $AZURE_SUBSCRIPTION_ID  --no-prompt
    azd env set AZURE_TENANT_ID $AZURE_TENANT_ID  --no-prompt
    azd env set AZURE_USE_APPLICATION_INSIGHTS $AZURE_USE_APPLICATION_INSIGHTS  --no-prompt
    azd env set BACKEND_URI $BACKEND_URI  --no-prompt
fi

echo ""
echo "Loading azd .env file from current environment"
echo ""

while IFS='=' read -r key value; do
    value=$(echo "$value" | sed 's/^"//' | sed 's/"$//')
    export "$key=$value"
done <<EOF
$(azd env get-values)
EOF

if [ $? -ne 0 ]; then
    echo "Failed to load environment variables from azd environment"
    exit $?
fi

echo 'Creating python virtual environment "backend/backend_env"'
python3 -m venv backend/backend_env

echo ""
echo "Restoring backend python packages"
echo ""

cd backend
./backend_env/bin/python -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to restore backend python packages"
    exit $?
fi

echo ""
echo "Restoring frontend npm packages"
echo ""

cd ../frontend
npm install
if [ $? -ne 0 ]; then
    echo "Failed to restore frontend npm packages"
    exit $?
fi

echo ""
echo "Building frontend"
echo ""

npm run build
if [ $? -ne 0 ]; then
    echo "Failed to build frontend"
    exit $?
fi

echo ""
echo "Starting backend"
echo ""

cd ../backend
./backend_env/bin/python -m quart --app main:app run --port 50505 --reload
if [ $? -ne 0 ]; then
    echo "Failed to start backend"
    exit $?
fi
