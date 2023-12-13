targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

param storageAccountName string = ''
param storageResourceGroupLocation string = location
param storageContainerName string = 'content'

// Optional parameters to override the default azd resource naming conventions. Update the main.parameters.json file to provide values. e.g.,:
// "resourceGroupName": {
//      "value": "myGroupName"
// }

param applicationInsightsDashboardName string = ''
param applicationInsightsName string = ''
param logAnalyticsName string = ''
param resourceGroupName string = ''
param apimServiceName string = ''

// Please provide these parameters if you want to use an existing Azure OpenAI resource
param openAiServiceName string = ''
param openAiResourceGroupName string = ''
param openAiResourceGroupLocation string = location
param aoaiCapacity int = 10

// Please provide these parameters if you need to create a new Azure OpenAI resource
param openAiSkuName string = 'S0'
param adaDeploymentName string = 'ada'
param adaModelName string = 'text-embedding-ada-002'
param chatGptDeploymentName string = 'chatgpt'
param chatGptModelName string = 'gpt-35-turbo'

param vnetAddressPrefix string = '10.0.0.0/16'

param subnetAddressPrefix1 string = '10.0.0.0/24'
param subnetAddressPrefix2 string = '10.0.1.0/24'

// params for api policy settings
@description('1つめのAzire OpenAIのリージョンを指定してください')
param aoaiFirstLocation string = 'xxxx'
@description('2つめのAzire OpenAIのリージョンを指定してください')
param aoaiSecondLocation string = 'xxxx'
@description('CORSオリジンとして許可するドメインを指定してください(*でも可)')
param corsOriginUrl string = '*'
@description('認可対象となるAzure ADに登録されたアプリのIDを指定してください（例: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx）')
param audienceAppId string = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
@description('認可対象となるをAzure ADに登録されたアプリのスコープ名を指定してください')
param scopeName string = 'chat'
@description('認証対象となるAzure ADのテナントIDを指定してください')
param tenantId string = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
//var resourceToken = 'ytatewaki101502'
var tags = { 'azd-env-name': environmentName }

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

//  Refer Azure OpenAI resource group if it is provided (if not provided, use the resource group created above)
resource openAiResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(openAiResourceGroupName)) {
  name: !empty(openAiResourceGroupName) ? openAiResourceGroupName : rg.name
}

module openAi1 'core/ai/cognitiveservices.bicep' = {
  name: 'openai1'
  scope: openAiResourceGroup
  params: {
    name: !empty(openAiServiceName) ? openAiServiceName : '${abbrs.cognitiveServicesAccounts}${resourceToken}-1'
    location: aoaiFirstLocation
    tags: tags
    sku: {
      name: openAiSkuName
      capacity: aoaiCapacity
    }
    deployments: [
      {
        name: adaDeploymentName
        model: {
          format: 'OpenAI'
          name: adaModelName
          version: '2'
        }
        sku: {
          name: 'Standard'
          capacity: aoaiCapacity
        }
      }

      {
        name: chatGptDeploymentName
        model: {
          format: 'OpenAI'
          name: chatGptModelName
          version: '0613'
        }
        sku: {
          name: 'Standard'
          capacity: aoaiCapacity
        }
      }
    ]
  }
}

module openAi2 'core/ai/cognitiveservices.bicep' = {
  name: 'openai2'
  scope: openAiResourceGroup
  params: {
    name: !empty(openAiServiceName) ? openAiServiceName : '${abbrs.cognitiveServicesAccounts}${resourceToken}-2'
    location: aoaiSecondLocation
    tags: tags
    sku: {
      name: openAiSkuName
      capacity: aoaiCapacity
    }
    deployments: [
      {
        name: adaDeploymentName
        model: {
          format: 'OpenAI'
          name: adaModelName
          version: '2'
        }
        sku: {
          name: 'Standard'
          capacity: aoaiCapacity
        }
      }

      {
        name: chatGptDeploymentName
        model: {
          format: 'OpenAI'
          name: chatGptModelName
          version: '0613'
        }
        sku: {
          name: 'Standard'
          capacity: aoaiCapacity
        }
      }
    ]
  }
}


// Storage Account
module storage 'core/storage/storage-account.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    name: !empty(storageAccountName) ? storageAccountName : '${abbrs.storageStorageAccounts}${resourceToken}'
    location: storageResourceGroupLocation
    tags: tags
    publicNetworkAccess: 'Enabled'
    sku: {
      name: 'Standard_ZRS'
    }
    deleteRetentionPolicy: {
      enabled: true
      days: 2
    }
    containers: [
      {
        name: storageContainerName
        publicAccess: 'None'
      }
    ]
  }
}

// ================================================================================================
// NETWORK
// ================================================================================================
module publicIP 'core/network/pip.bicep' = {
  name: '${abbrs.networkPublicIPAddresses}${resourceToken}'
  scope: rg
  params: {
    name: '${abbrs.networkPublicIPAddresses}${resourceToken}'
    location: location
    domainNameLabel: '${abbrs.networkApplicationGateways}${resourceToken}'
  }
}

module vnet 'core/network/vnet.bicep' = {
  name: '${abbrs.networkVirtualNetworks}${resourceToken}'
  scope: rg
  params: {
    name: '${abbrs.networkVirtualNetworks}${resourceToken}'
    location: location
    addressPrefixes: [vnetAddressPrefix]
  }
}

module nsgPublic 'core/network/nsgPublic.bicep' = {
  name: '${abbrs.networkNetworkSecurityGroups}public-${resourceToken}'
  scope: rg
  params: {
    name: '${abbrs.networkNetworkSecurityGroups}public-${resourceToken}'
    location: location
  }
}

module nsgPrivate 'core/network/nsgPrivate.bicep' = {
  name: '${abbrs.networkNetworkSecurityGroups}private-${resourceToken}'
  scope: rg
  params: {
    name: '${abbrs.networkNetworkSecurityGroups}private-${resourceToken}'
    location: location
  }
}

module PublicSubnet 'core/network/subnet.bicep' = {
  name: '${abbrs.networkVirtualNetworksSubnets}public-${resourceToken}'
  scope: rg
  params: {
    existVnetName: vnet.outputs.name
    name: '${abbrs.networkVirtualNetworksSubnets}public-${resourceToken}'
    addressPrefix: subnetAddressPrefix1
    networkSecurityGroup: {
      id: nsgPublic.outputs.id
    }
  }
  dependsOn: [
    vnet
  ]
}

module PrivateSubnet 'core/network/subnet.bicep' = {
  name: '${abbrs.networkVirtualNetworksSubnets}private-${resourceToken}'
  scope: rg
  params: {
    existVnetName: vnet.outputs.name
    name: '${abbrs.networkVirtualNetworksSubnets}private-${resourceToken}'
    addressPrefix: subnetAddressPrefix2
    networkSecurityGroup: {
      id: nsgPrivate.outputs.id
    }
  }
  dependsOn: [
    vnet
    PublicSubnet
  ]
}

// ================================================================================================
// PRIVATE ENDPOINT
// ================================================================================================
module oepnaiPrivateEndopoint 'core/network/privateEndpoint.bicep' = {
  name: '${abbrs.networkPrivateLinkServices}${resourceToken}'
  scope: rg
  params: {
    location: location
    name: '${abbrs.networkPrivateLinkServices}${resourceToken}'
    subnetId: PrivateSubnet.outputs.id
    privateLinkServiceIdopenAi1: openAi1.outputs.id
    privateLinkServiceIdopenAi2: openAi2.outputs.id
    privateLinkServiceGroupIds: ['account']
    dnsZoneName: 'openai.azure.com'
    linkVnetId: vnet.outputs.id
  }
  dependsOn: [
    vnet
    PrivateSubnet
    openAi1
    openAi2
  ]
}



// ================================================================================================
// APPLICATION GATEWAY
// ================================================================================================
module agw './core/gateway/agw.bicep' = {
  name: '${abbrs.networkApplicationGateways}${resourceToken}'
  scope: rg
  params: {
    VnetName: vnet.outputs.name
    SnetName: PublicSubnet.outputs.name
    location: location
    name: '${abbrs.networkApplicationGateways}${resourceToken}'
    publicIPName: publicIP.outputs.name
    OpenaiName: '${abbrs.cognitiveServicesAccounts}${resourceToken}'

  }
  dependsOn: [
    vnet
    PublicSubnet
    publicIP
    oepnaiPrivateEndopoint
  ]
}


// Monitor application with Azure Monitor
module monitoring './core/monitor/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    location: location
    tags: tags
    logAnalyticsName: !empty(logAnalyticsName) ? logAnalyticsName : '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    applicationInsightsName: !empty(applicationInsightsName) ? applicationInsightsName : '${abbrs.insightsComponents}${resourceToken}'
    applicationInsightsDashboardName: !empty(applicationInsightsDashboardName) ? applicationInsightsDashboardName : '${abbrs.portalDashboards}${resourceToken}'
  }
}

// Creates Azure API Management (APIM) service to mediate the requests between the frontend and the backend API
module apim './core/gateway/apim.bicep' = {
  name: 'apim-deployment'
  scope: rg

  params: {
    name: !empty(apimServiceName) ? apimServiceName : '${abbrs.apiManagementService}${resourceToken}'
    location: location
    tags: tags
    sku: 'Standard'
    skuCount: 1
    applicationInsightsName: monitoring.outputs.applicationInsightsName
    workspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    storageAccountId: storage.outputs.id
  }
}


// Assigns a role to Azure OpenAI API Management service to access Azure OpenAI
module aoaiRole 'core/security/role.bicep' = {
  scope: openAiResourceGroup
  name: 'search-role-backend'
  params: {
    principalId: apim.outputs.identityPrincipalId
    // Cognitive Services OpenAI user
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: 'ServicePrincipal'
  }
}


// Configures the API in the Azure API Management (APIM) service
module apimApi './app/apim-api.bicep' = {
  name: 'apim-api-deployment'
  scope: rg
  dependsOn: [
    apim
    agw
  ]
  params: {
    name: apim.outputs.apimServiceName
    apiName: 'azure-openai-api'
    apiDisplayName: 'Azure OpenAI API'
    apiDescription: 'This is proxy endpoints for Azure OpenAI API'
    apiPath: 'api'

    //API Policy parameters
    corsOriginUrl: corsOriginUrl
    audienceAppId: audienceAppId
    scopeName: scopeName
    apiBackendUrl: 'https://${abbrs.networkApplicationGateways}${resourceToken}.${location}.cloudapp.azure.com/openai'
    tenantId: tenantId
  }
}

// App outputs
output APPLICATIONINSIGHTS_CONNECTION_STRING string = monitoring.outputs.applicationInsightsConnectionString
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output REACT_APP_APPLICATIONINSIGHTS_CONNECTION_STRING string = monitoring.outputs.applicationInsightsConnectionString
