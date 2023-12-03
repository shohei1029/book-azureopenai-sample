#!/bin/bash
# Azureで作成したサービスプリンシパル <object_id> に役割を割り当てる
#
# Prerequirement: サービスプリンシパルをあらかじめ作成しオブジェクトIDを取得しておく
# $ export AZURE_SUBSCRIPTION_ID=<subscrition_id>
# $ export AZURE_RESOURCE_GROUP=<resource_group_name>
# $ export AZURE_SERVICE_PRINCIPAL_NAME=<service_principal_name>
# $ az ad sp create-for-rbac --name $AZURE_SERVICE_PRINCIPAL_NAME --role owner --scopes /subscriptions/$AZURE_SUBSCRIPTION_ID/resourceGroups/$AZURE_RESOURCE_GROUP --json-auth
# $ az ad sp show --id <client_id> --query "id" # This command can get the <object_id>
#
# Usage:
# scripts/roles.sh -g <resource_group_name> -p <object_id> -s <subscrption_id>
#

set -e

while getopts g:p:s: OPT; do
    case $OPT in
    "g")
        FLG_G="TRUE"
        AZURE_RESOURCE_GROUP="$OPTARG"
        ;;
    "p")
        FLG_P="TRUE"
        AZURE_PRINCIPAL_ID="$OPTARG"
        ;;
    "s")
        FLG_S="TRUE"
        AZURE_SUBSCRIPTION_ID="$OPTARG"
        ;;
    *)
        echo -e "Usage: scripts/roles.sh [-g AZURE_RESOURCE_GROUP(Default: rg-demo)] [-p AZURE_PRINCIPAL_ID(Default: b57991a6-c7c6-4cce-8a3a-5b6eaceacf8c)] [-s AZURE_SUBSCRIPTION_ID(Default: 0bf5bc92-8ea2-4160-a704-7130857f3ba3)]" 1>&2
        exit 1
        ;;
    esac
done

if [ "$FLG_G" != "TRUE" ]; then
    AZURE_RESOURCE_GROUP=rg-demo
fi

if [ "$FLG_P" != "TRUE" ]; then
    AZURE_PRINCIPAL_ID=b57991a6-c7c6-4cce-8a3a-5b6eaceacf8c
fi

if [ "$FLG_S" != "TRUE" ]; then
    AZURE_SUBSCRIPTION_ID=0bf5bc92-8ea2-4160-a704-7130857f3ba3
fi

# memo: https://docs.microsoft.com/ja-jp/azure/role-based-access-control/built-in-roles
# "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd" Cognitive Services OpenAI User https://www.azadvertizer.net/azrolesadvertizer/5e0bd9bd-7b93-4f28-af87-19fc36ad61bd.html
# "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1" Storage Blob Data Reader https://www.azadvertizer.net/azrolesadvertizer/2a2b9908-6ea1-4ae2-8e65-a410df84e7d1.html
# "ba92f5b4-2d11-453d-a403-e96b0029c9fe" Storage Blob Data Contributor https://www.azadvertizer.net/azrolesadvertizer/ba92f5b4-2d11-453d-a403-e96b0029c9fe.html
# "1407120a-92aa-4202-b7e9-c0e197c71c8f" Search Index Data Reader https://www.azadvertizer.net/azrolesadvertizer/1407120a-92aa-4202-b7e9-c0e197c71c8f.html
# "8ebe5a00-799e-43f5-93ac-243d3dce84a7" Search Index Data Contributor https://www.azadvertizer.net/azrolesadvertizer/8ebe5a00-799e-43f5-93ac-243d3dce84a7.html
roles=(
    "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd"
    "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1"
    "ba92f5b4-2d11-453d-a403-e96b0029c9fe"
    "1407120a-92aa-4202-b7e9-c0e197c71c8f"
    "8ebe5a00-799e-43f5-93ac-243d3dce84a7"
)

for role in "${roles[@]}"; do
    echo "az role assignment create --role $role --assignee-object-id $AZURE_PRINCIPAL_ID --scope /subscriptions/$AZURE_SUBSCRIPTION_ID/resourceGroups/$AZURE_RESOURCE_GROUP --assignee-principal-type ServicePrincipal"
    az role assignment create \
        --role $role \
        --assignee-object-id $AZURE_PRINCIPAL_ID \
        --scope /subscriptions/$AZURE_SUBSCRIPTION_ID/resourceGroups/$AZURE_RESOURCE_GROUP \
        --assignee-principal-type ServicePrincipal
done
