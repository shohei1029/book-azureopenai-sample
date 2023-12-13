param location string = resourceGroup().location
param dnsZoneName string
param linkVnetId string
param name string
param subnetId string
param privateLinkServiceIdopenAi1 string
param privateLinkServiceIdopenAi2 string
param privateLinkServiceGroupIds array
//param isPrivateNetworkEnabled bool

//resource privateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (isPrivateNetworkEnabled) {
resource privateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.${dnsZoneName}'
  location: 'global'
}

//resource virtualNetworkLinks 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (isPrivateNetworkEnabled) {
resource virtualNetworkLinks 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  name: 'vnet-link-${name}'
  location: 'global'
  parent: privateDnsZone
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: linkVnetId
    }
  }
}

// https://github.com/MicrosoftDocs/azure-docs/blob/main/articles/private-link/private-endpoint-overview.md
resource privateEndpoint1 'Microsoft.Network/privateEndpoints@2023-02-01' = {
  name: '${name}-1'
  location: location
  properties: {
    subnet: {
      id: subnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${name}-connection-1}'
        properties: {
          privateLinkServiceId: privateLinkServiceIdopenAi1
          groupIds: privateLinkServiceGroupIds
        }
      }
    ]
  }
}

resource privateEndpoint2 'Microsoft.Network/privateEndpoints@2023-02-01' = {
  name: '${name}-2'
  location: location
  properties: {
    subnet: {
      id: subnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${name}-connection-2}'
        properties: {
          privateLinkServiceId: privateLinkServiceIdopenAi2
          groupIds: privateLinkServiceGroupIds
        }
      }
    ]
  }
}

resource privateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-04-01' = {
  parent: privateEndpoint1
  name: privateDnsZone.name
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'private-link-${name}'
        properties: {
          privateDnsZoneId: privateDnsZone.id
        }
      }
    ]
  }
}

resource privateDnsZoneGroup2 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-04-01' = {
  parent: privateEndpoint2
  name: privateDnsZone.name
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'private-link-${name}-2'
        properties: {
          privateDnsZoneId: privateDnsZone.id
        }
      }
    ]
  }
}

output privateEndpointId1 string = privateEndpoint1.id
output privateEndpointName1 string = privateEndpoint1.name
output privateEndpointId2 string = privateEndpoint2.id
output privateEndpointName2 string = privateEndpoint2.name
