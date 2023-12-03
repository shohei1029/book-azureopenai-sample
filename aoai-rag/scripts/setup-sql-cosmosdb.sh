#!/usr/bin/env bash
resourceGroup=$1
accountName="openai-demo-cosmosdb-$(openssl rand -hex 5)"
databaseName=ChatGPT
containerName=ChatLogs
echo
echo "Creating Cosmos DB..."

az cosmosdb create --name $accountName --resource-group $resourceGroup
az cosmosdb sql database create --name $databaseName --account-name $accountName --resource-group $resourceGroup
az cosmosdb sql container create --name $containerName --partition-key-path "/id" --database-name $databaseName --account-name $accountName --resource-group $resourceGroup
keys_json=$(az cosmosdb keys list --name $accountName --resource-group $resourceGroup --type keys)
key=$( echo $keys_json | jq -r '.primaryMasterKey')
con_string_json=$(az cosmosdb keys list --name $accountName --resource-group $resourceGroup --type connection-strings)
con_string=$( echo $con_string_json | jq -r '.connectionStrings[0].connectionString')

echo
echo "Done!"
echo
echo "Make a note of the following values for use in the rest of this exercise:"
echo
echo "Account ID: $accountName"
echo
echo "Database Name: $databaseName"
echo
echo "Container Name: $containerName"
echo
echo "Access Key: $key"
echo
echo "Connection String: $con_string"
echo