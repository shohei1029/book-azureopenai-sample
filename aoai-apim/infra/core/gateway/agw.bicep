param name string
param location string
param VnetName string
param SnetName string
param publicIPName string
param OpenaiName string

resource agwService 'Microsoft.Network/applicationGateways@2023-05-01' = {
  name: name
  location: location
  properties: {
    sku: {
      name: 'Standard_v2'
      tier: 'Standard_v2'
    }
    gatewayIPConfigurations: [
      {
        name: 'appGatewayIpConfig'
        properties: {
          subnet: {
            id: resourceId('Microsoft.Network/virtualNetworks/subnets', VnetName, SnetName)
          }
        }
      }
    ]
    sslCertificates: [
      {
        name: 'agw-https-cerificate'
        properties: {
          data: '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'
          password: 'H1STReAuATvkLimx'
        }
      }
    ]
    trustedRootCertificates: [
      {
        name: 'agw-https-cerificate'
        properties: {
          data: 'MIIDMDCCAhigAwIBAgIQQLSL67HwcqdC9K6L59Ee/TANBgkqhkiG9w0BAQsFADAcMRowGAYDVQQDDBFNeSBSb290IEF1dGhvcml0eTAeFw0yMzEwMDgwNTI1MzZaFw0zMzEwMDgwNTM1MzZaMBwxGjAYBgNVBAMMEU15IFJvb3QgQXV0aG9yaXR5MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA35frmIiMdXcbxUU1sPMPP+lI9m/JoioDciTbO/o0slDAASdTGesTO0UMKC3jY05OgT0CivI7g1Uj/BxRAO0SPSkSA10m3PwIN/gsTX8I9zYNlVxrSmgawHCFoP/wv8ipHAnrhuHLm6N9pPfbkz7CSjPAfdUP6/KxrI3D6qo8CLkA3jOgiAtN/I2hbtIBIfS7vhHHqUaNZDy4BpA01bGhITtbW8c79wP8K2eNqZpWXfHqg9vvP5JczdMls0OuPT8yxTg8HgSIsSwUuKaDcEYaX9CC1RS4lWJtlfUNFgs8TLyRyYTs1z1F8ejVZeMvygcjg933VSsmW2W/TpJvDfqfQQIDAQABo24wbDAOBgNVHQ8BAf8EBAMCAYYwHQYDVR0lBBYwFAYIKwYBBQUHAwIGCCsGAQUFBwMBMBwGA1UdEQQVMBOCEU15IFJvb3QgQXV0aG9yaXR5MB0GA1UdDgQWBBQUmrCR848AJclvVYMBN2FKzTRVmzANBgkqhkiG9w0BAQsFAAOCAQEAiwvjgYCzwks4A1TmNr0n5B6/Wxg+4AhrIvOo9sgxzvrg22Y3heuSFhQh4gcm9dNaHTDFqgk8J4bVa0e12a8YoyU9GRSS2MfV45Y3V21aM6DhuyxpAz1Z6wP0IN9O8TUcqwEmr00bbwIMYECEtyHhuJCYcqknRommEVaz7F57+nQmGaVcGW1QWFiWD9ERuKTVQx/iR9ZeQKZZ+eOkKjFC1NMS2eezs3efrCHsXvHuk+naJ/Z94vKaoSgOwgdAXgxAphYdc0XKa+6LKwTVLxr5Qdje+C4EXooTxbgEwMTqgmzyANzPGlGrqv5udIPFybDoIjAvX4YHHfDng2tm6ND2Gg=='
        }
      }
    ]
    trustedClientCertificates: []
    sslProfiles: []
    frontendIPConfigurations: [
      {
        name: 'appGwPublicFrontendIpIPv4'
        properties: {
          publicIPAddress: {
            id: resourceId('Microsoft.Network/publicIPAddresses', publicIPName)
          }
        }
      }
    ]
    frontendPorts: [
      {
        name: 'port_443'
        properties: {
          port: 443
        }
      }
    ]
    backendAddressPools: [
      {
        name: 'openai-pool'
        properties: {
          backendAddresses: [
            {
              fqdn: '${OpenaiName}-1.openai.azure.com'
            }
            {
              fqdn: '${OpenaiName}-2.openai.azure.com'
            }
          ]
        }
      }
    ]
    loadDistributionPolicies: []
    backendHttpSettingsCollection: [
      {
        name: 'https'
        properties: {
          port: 443
          protocol: 'Https'
          cookieBasedAffinity: 'Disabled'
          pickHostNameFromBackendAddress: true
          affinityCookieName: 'ApplicationGatewayAffinity'
          requestTimeout: 20
          probe: {
            id: resourceId('Microsoft.Network/applicationGateways/probes', name, 'https')
          }
        }
      }
    ]
    backendSettingsCollection: []
    httpListeners: [
      {
        name: 'https'
        properties: {
          frontendIPConfiguration: {
            id: resourceId('Microsoft.Network/applicationGateways/frontendIPConfigurations', name, 'appGwPublicFrontendIpIPv4')
          }
          frontendPort: {
            id: resourceId('Microsoft.Network/applicationGateways/frontendPorts', name, 'port_443')
          }
          protocol: 'Https'
          sslCertificate: {
            id: resourceId('Microsoft.Network/applicationGateways/sslCertificates', name, 'agw-https-cerificate')
          }
          hostNames: []
          requireServerNameIndication: false
          customErrorConfigurations: []
        }
      }
    ]
    listeners: []
    urlPathMaps: []
    requestRoutingRules: [
      {
        name: 'https'
        properties: {
          ruleType: 'Basic'
          priority: 19999
          httpListener: {
            id: resourceId('Microsoft.Network/applicationGateways/httpListeners', name, 'https')
          }
          backendAddressPool: {
            id: resourceId('Microsoft.Network/applicationGateways/backendAddressPools', name, 'openai-pool')
          }
          backendHttpSettings: {
            id: resourceId('Microsoft.Network/applicationGateways/backendHttpSettingsCollection', name, 'https')
          }
        }
      }
    ]
    routingRules: []
    probes: [
      {
        name: 'https'
        properties: {
          protocol: 'Https'
          path: '/status-0123456789abcdef'
          interval: 30
          timeout: 30
          unhealthyThreshold: 3
          pickHostNameFromBackendHttpSettings: true
          minServers: 0
          match: {
            statusCodes: [
              '200-399'
            ]
          }
        }
      }
    ]
    rewriteRuleSets: []
    redirectConfigurations: []
    privateLinkConfigurations: []
    enableHttp2: true
    autoscaleConfiguration: {
      minCapacity: 0
      maxCapacity: 10
    }
  }
}
