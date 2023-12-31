param existVnetName string
param name string
param addressPrefix string
param networkSecurityGroup object = {}
param delegations array = []
//param isPrivateNetworkEnabled bool

//resource existVnet 'Microsoft.Network/virtualNetworks@2021-02-01' existing = if (isPrivateNetworkEnabled) {
resource existVnet 'Microsoft.Network/virtualNetworks@2021-02-01' existing = {
  scope: resourceGroup()
  name: existVnetName
}

//resource subnet 'Microsoft.Network/virtualNetworks/subnets@2023-02-01' = if (isPrivateNetworkEnabled) {
resource subnet 'Microsoft.Network/virtualNetworks/subnets@2023-02-01' = {
  parent: existVnet
  name: name
  properties: {
    addressPrefix: addressPrefix
    networkSecurityGroup: networkSecurityGroup != null ? {
      id: networkSecurityGroup.id
    } : null
    delegations: delegations
  }
}

output id string = subnet.id
output name string = subnet.name
