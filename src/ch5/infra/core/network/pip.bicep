param name string
param location string
param domainNameLabel string
//param isPrivateNetworkEnabled bool

resource publicIP 'Microsoft.Network/publicIPAddresses@2023-05-01' = {
  name: name
  location: location
  sku: {
    name: 'Standard'
    tier: 'Regional'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
    dnsSettings: {
      domainNameLabel: domainNameLabel
      fqdn: '${domainNameLabel}.${location}.cloudapp.azure.com'
    }
  }
}

output id string = publicIP.id
output name string = publicIP.name

// output publicIPAddress string = publicIP.properties.ipAddress
