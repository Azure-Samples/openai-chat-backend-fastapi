targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name which is used to generate a short unique hash for each resource')
param name string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Id of the user or app to assign application roles')
param principalId string = ''

@description('Flag to decide whether to create a role assignment for the user and app')
param useKeylessAuth bool

param acaExists bool = false
param allowedOrigins string = ''

param openAiResourceName string = ''
param openAiResourceGroupName string = ''
@description('Location for the OpenAI resource group')
@allowed([ 'canadaeast', 'eastus', 'eastus2', 'francecentral', 'switzerlandnorth', 'uksouth', 'japaneast', 'northcentralus', 'australiaeast', 'swedencentral' ])
@metadata({
  azd: {
    type: 'location'
  }
})
param openAiResourceLocation string
param openAiSkuName string = ''
param openAiDeploymentCapacity int = 30

@description('Whether the deployment is running on GitHub Actions')
param runningOnGh string = ''

var resourceToken = toLower(uniqueString(subscription().id, name, location))
var tags = { 'azd-env-name': name }

resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: '${name}-rg'
  location: location
  tags: tags
}

resource openAiResourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = if (!empty(openAiResourceGroupName)) {
  name: !empty(openAiResourceGroupName) ? openAiResourceGroupName : resourceGroup.name
}

var prefix = '${name}-${resourceToken}'

var openAiDeploymentName = 'chatgpt'

module openAi 'br/public:avm/res/cognitive-services/account:0.7.2' = {
  name: 'openai'
  scope: openAiResourceGroup
  params: {
    name: !empty(openAiResourceName) ? openAiResourceName : '${resourceToken}-cog'
    location: !empty(openAiResourceLocation) ? openAiResourceLocation : location
    tags: tags
    kind: 'OpenAI'
    customSubDomainName: !empty(openAiResourceName) ? openAiResourceName : '${resourceToken}-cog'
    publicNetworkAccess: 'Disabled'  // Changed to Disabled to enforce private endpoint access
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
    sku: !empty(openAiSkuName) ? openAiSkuName : 'S0'
    deployments: [
      {
        name: openAiDeploymentName
        model: {
          format: 'OpenAI'
          name: 'gpt-4o-mini'
          version: '2024-07-18'
        }
        sku: {
          name: 'GlobalStandard'
          capacity: openAiDeploymentCapacity
        }
      }
    ]
    disableLocalAuth: useKeylessAuth
  }
}

module logAnalyticsWorkspace 'br/public:avm/res/operational-insights/workspace:0.7.0' = {
  name: 'loganalytics'
  scope: resourceGroup
  params: {
    name: '${prefix}-loganalytics'
    location: location
    tags: tags
    skuName: 'PerGB2018'
    dataRetention: 30
    publicNetworkAccessForIngestion: 'Disabled'
    publicNetworkAccessForQuery: 'Disabled'
    useResourcePermissions: true
  }
}


// Virtual network for all resources
module virtualNetwork 'br/public:avm/res/network/virtual-network:0.6.1' = {
  name: 'vnet'
  scope: resourceGroup
  params: {
    name: '${prefix}-vnet'
    location: location
    tags: tags
    addressPrefixes: [
      '10.0.0.0/16'
    ]
    subnets: [
      {
        name: 'container-apps-subnet'
        addressPrefix: '10.0.0.0/21'
      }
      {
        name: 'private-endpoints-subnet'
        addressPrefix: '10.0.8.0/24'
        privateEndpointNetworkPolicies: 'Enabled'
        privateLinkServiceNetworkPolicies: 'Enabled'
      }
    ]
  }
}

// Azure OpenAI Private DNS Zone
module openAiPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.7.1' = {
  name: 'openai-dns-zone'
  scope: resourceGroup
  params: {
    name: 'privatelink.openai.azure.com'
    tags: tags
    virtualNetworkLinks: [
      {
        registrationEnabled: false
        virtualNetworkResourceId: virtualNetwork.outputs.resourceId
      }
    ]
  }
}

// Log Analytics Private DNS Zone
module logAnalyticsPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.7.1' = {
  name: 'log-analytics-dns-zone'
  scope: resourceGroup
  params: {
    name: 'privatelink.oms.opinsights.azure.com'
    tags: tags
    virtualNetworkLinks: [
      {
        registrationEnabled: false
        virtualNetworkResourceId: virtualNetwork.outputs.resourceId
      }
    ]
  }
}

// Additional Log Analytics Private DNS Zone for query endpoint
module logAnalyticsQueryPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.7.1' = {
  name: 'log-analytics-query-dns-zone'
  scope: resourceGroup
  params: {
    name: 'privatelink.ods.opinsights.azure.com'
    tags: tags
    virtualNetworkLinks: [
      {
        registrationEnabled: false
        virtualNetworkResourceId: virtualNetwork.outputs.resourceId
      }
    ]
  }
}

// Additional Log Analytics Private DNS Zone for agent service
module logAnalyticsAgentPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.7.1' = {
  name: 'log-analytics-agent-dns-zone'
  scope: resourceGroup
  params: {
    name: 'privatelink.agentsvc.azure-automation.net'
    tags: tags
    virtualNetworkLinks: [
      {
        registrationEnabled: false
        virtualNetworkResourceId: virtualNetwork.outputs.resourceId
      }
    ]
  }
}

// Azure Monitor Private DNS Zone
module monitorPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.7.1' = {
  name: 'monitor-dns-zone'
  scope: resourceGroup
  params: {
    name: 'privatelink.monitor.azure.com'
    tags: tags
    virtualNetworkLinks: [
      {
        registrationEnabled: false
        virtualNetworkResourceId: virtualNetwork.outputs.resourceId
      }
    ]
  }
}

// Storage Blob Private DNS Zone for Log Analytics solution packs
module blobPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.7.1' = {
  name: 'blob-dns-zone'
  scope: resourceGroup
  params: {
    name: 'privatelink.blob.core.windows.net'
    tags: tags
    virtualNetworkLinks: [
      {
        registrationEnabled: false
        virtualNetworkResourceId: virtualNetwork.outputs.resourceId
      }
    ]
  }
}

// Azure Container Registry Private DNS Zone
module acrPrivateDnsZone 'br/public:avm/res/network/private-dns-zone:0.7.1' = {
  name: 'acr-dns-zone'
  scope: resourceGroup
  params: {
    name: 'privatelink.azurecr.io'
    tags: tags
    virtualNetworkLinks: [
      {
        registrationEnabled: false
        virtualNetworkResourceId: virtualNetwork.outputs.resourceId
      }
    ]
  }
}

module privateEndpoint 'br/public:avm/res/network/private-endpoint:0.11.0' = {
  name: 'privateEndpointDeployment'
  scope: resourceGroup
  params: {
    name: '${prefix}-openai-pe'
    location: location
    tags: tags
    subnetResourceId: virtualNetwork.outputs.subnetResourceIds[1]
    privateDnsZoneGroup: {
      privateDnsZoneGroupConfigs: [
        {
          privateDnsZoneResourceId: openAiPrivateDnsZone.outputs.resourceId
        }
      ]
    }
    privateLinkServiceConnections: [
      {
        name: '${prefix}-openai-pe'
        properties: {
          groupIds: [
            'account'
          ]
          privateLinkServiceId: openAi.outputs.resourceId
        }
      }
    ]
  }
}

// Azure Monitor Private Link Scope
module monitorPrivateLinkScope 'br/public:avm/res/insights/private-link-scope:0.7.1' = {
  name: 'monitor-private-link-scope'
  scope: resourceGroup
  params: {
    name: '${prefix}-ampls'
    location: 'global'
    tags: tags
    accessModeSettings: {
      ingestionAccessMode: 'PrivateOnly'
      queryAccessMode: 'PrivateOnly'
    }
    scopedResources: [
      {
        name: 'loganalytics-scoped-resource'
        linkedResourceId: logAnalyticsWorkspace.outputs.resourceId
      }
    ]
    privateEndpoints: [
      {
        name: 'loganalytics-private-endpoint'
        subnetResourceId: virtualNetwork.outputs.subnetResourceIds[1]
        privateDnsZoneGroup: {
          privateDnsZoneGroupConfigs: [
            {
              privateDnsZoneResourceId: monitorPrivateDnsZone.outputs.resourceId
            }
            {
              privateDnsZoneResourceId: logAnalyticsPrivateDnsZone.outputs.resourceId
            }
            {
              privateDnsZoneResourceId: logAnalyticsQueryPrivateDnsZone.outputs.resourceId
            }
            {
              privateDnsZoneResourceId: logAnalyticsAgentPrivateDnsZone.outputs.resourceId
            }
            {
              privateDnsZoneResourceId: blobPrivateDnsZone.outputs.resourceId
            }
          ]
        }
      }
    ]
  }
}

// Container apps host (including container registry)
module containerApps 'core/host/container-apps.bicep' = {
  name: 'container-apps'
  scope: resourceGroup
  params: {
    name: 'app'
    location: location
    tags: tags
    containerAppsEnvironmentName: '${prefix}-containerapps-env'
    containerRegistryName: '${replace(prefix, '-', '')}registry'
    logAnalyticsWorkspaceName: logAnalyticsWorkspace.outputs.name
    // Reference the virtual network
    vnetName: virtualNetwork.outputs.name
    subnetName: virtualNetwork.outputs.subnetNames[0]
  }
}

// Container Registry Private Endpoint
module acrPrivateEndpoint 'br/public:avm/res/network/private-endpoint:0.11.0' = {
  name: 'acrPrivateEndpointDeployment'
  scope: resourceGroup
  params: {
    name: '${prefix}-acr-pe'
    location: location
    tags: tags
    subnetResourceId: virtualNetwork.outputs.subnetResourceIds[1]
    privateDnsZoneGroup: {
      privateDnsZoneGroupConfigs: [
        {
          privateDnsZoneResourceId: acrPrivateDnsZone.outputs.resourceId
        }
      ]
    }
    privateLinkServiceConnections: [
      {
        name: '${prefix}-acr-pe'
        properties: {
          groupIds: [
            'registry'
          ]
          privateLinkServiceId: containerApps.outputs.registryId
        }
      }
    ]
  }
}

// Container app frontend
module aca 'aca.bicep' = {
  name: 'aca'
  scope: resourceGroup
  params: {
    name: replace('${take(prefix,19)}-ca', '--', '-')
    location: location
    tags: tags
    identityName: '${prefix}-id-aca'
    containerAppsEnvironmentName: containerApps.outputs.environmentName
    containerRegistryName: containerApps.outputs.registryName
    openAiDeploymentName: openAiDeploymentName
    openAiEndpoint: openAi.outputs.endpoint
    openAiResourceName: openAi.outputs.name
    allowedOrigins: allowedOrigins
    exists: acaExists
  }
}

module openAiRoleUser 'core/security/role.bicep' = if (useKeylessAuth && empty(runningOnGh)) {
  scope: openAiResourceGroup
  name: 'openai-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: 'User'
  }
}

module openAiRoleBackend 'core/security/role.bicep' = if (useKeylessAuth) {
  scope: openAiResourceGroup
  name: 'openai-role-backend'
  params: {
    principalId: aca.outputs.SERVICE_ACA_IDENTITY_PRINCIPAL_ID
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
    principalType: 'ServicePrincipal'
  }
}

output AZURE_LOCATION string = location

output AZURE_OPENAI_CHATGPT_DEPLOYMENT string = openAiDeploymentName
output AZURE_OPENAI_ENDPOINT string = openAi.outputs.endpoint
output AZURE_OPENAI_RESOURCE string = openAi.outputs.name
output AZURE_OPENAI_RESOURCE_LOCATION string = openAi.outputs.location
output AZURE_OPENAI_RESOURCE_GROUP string = openAiResourceGroup.name

output SERVICE_ACA_IDENTITY_PRINCIPAL_ID string = aca.outputs.SERVICE_ACA_IDENTITY_PRINCIPAL_ID
output SERVICE_ACA_NAME string = aca.outputs.SERVICE_ACA_NAME
output SERVICE_ACA_URI string = aca.outputs.SERVICE_ACA_URI
output SERVICE_ACA_IMAGE_NAME string = aca.outputs.SERVICE_ACA_IMAGE_NAME

output AZURE_CONTAINER_ENVIRONMENT_NAME string = containerApps.outputs.environmentName
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerApps.outputs.registryLoginServer
output AZURE_CONTAINER_REGISTRY_NAME string = containerApps.outputs.registryName
