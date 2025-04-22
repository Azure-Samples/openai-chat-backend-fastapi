param name string
param location string = resourceGroup().location
param tags object = {}

param daprEnabled bool = false
param logAnalyticsWorkspaceName string
param applicationInsightsName string = ''

@description('Virtual network name for container apps environment.')
param vnetName string = ''
@description('Subnet name for container apps environment integration.')
param subnetName string = ''

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2022-03-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
    daprAIInstrumentationKey: daprEnabled && !empty(applicationInsightsName) ? applicationInsights.properties.InstrumentationKey : ''
    vnetConfiguration: (!empty(vnetName) && !empty(subnetName)) ? {
      // Use proper subnet resource ID format
      infrastructureSubnetId: resourceId('Microsoft.Network/virtualNetworks/subnets', vnetName, subnetName)
      internal: false // TODO: Make this a parameter
    } : null
  }
}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' existing = {
  name: logAnalyticsWorkspaceName
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = if (daprEnabled && !empty(applicationInsightsName)){
  name: applicationInsightsName
}

// Use separate resource references instead of parent/child relationship
resource virtualNetwork 'Microsoft.Network/virtualNetworks@2023-05-01' existing = if (!empty(vnetName)) {
  name: vnetName
}

output defaultDomain string = containerAppsEnvironment.properties.defaultDomain
output name string = containerAppsEnvironment.name
