param name string
param location string

resource nsg 'Microsoft.Network/networkSecurityGroups@2023-05-01' =  {
  name: name
  location: location
}

output id string = nsg.id
