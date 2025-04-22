param name string
param location string = resourceGroup().location
param tags object = {}

@description('Address prefixes for the virtual network.')
param addressPrefixes array

@description('Subnets to be created within the virtual network.')
param subnets array

@description('DNS servers to be configured for the virtual network. Default is Azure DNS.')
param dnsServers array = []

@description('Enable DDoS Protection Standard on the virtual network.')
param enableDdosProtection bool = false

resource virtualNetwork 'Microsoft.Network/virtualNetworks@2023-05-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: addressPrefixes
    }
    dhcpOptions: !empty(dnsServers) ? {
      dnsServers: dnsServers
    } : null
    enableDdosProtection: enableDdosProtection
    subnets: [for subnet in subnets: {
      name: subnet.name
      properties: {
        addressPrefix: subnet.addressPrefix
        delegations: contains(subnet, 'delegations') ? subnet.delegations : []
        networkSecurityGroup: contains(subnet, 'networkSecurityGroupId') ? {
          id: subnet.networkSecurityGroupId
        } : null
        routeTable: contains(subnet, 'routeTableId') ? {
          id: subnet.routeTableId
        } : null
        serviceEndpoints: contains(subnet, 'serviceEndpoints') ? subnet.serviceEndpoints : []
        privateEndpointNetworkPolicies: contains(subnet, 'privateEndpointNetworkPolicies') ? subnet.privateEndpointNetworkPolicies : null
      }
    }]
  }
}

// Outputs for use in other modules
output id string = virtualNetwork.id
output name string = virtualNetwork.name
output subnets array = virtualNetwork.properties.subnets
