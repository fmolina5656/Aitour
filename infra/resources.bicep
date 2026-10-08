// Recursos del stand: Foundry (cuenta + proyecto + modelos + guardrail), observabilidad,
// Container Apps con Managed Identity, registro de imágenes y Azure Files para /data.
param environmentName string
param location string
param tags object
param principalId string
param modelDeployments array
@secure()
param leadSecret string
@secure()
param powerAutomateUrl string
param modelArquitecto string
param modelFinanciero string
param modelRiesgo string
param modelDiagramador string
param modelRedactor string
param modelGuard string

var token = toLower(uniqueString(subscription().id, resourceGroup().id, environmentName))
var foundryName = 'rm-foundry-${token}'
var projectName = 'aitour'
var appName = 'rm-aitour-${take(token, 8)}'
var guardrailName = 'readymind-stand'

// Roles (IDs integrados de Azure)
var roleAzureAIUser = '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Azure AI User (Foundry User): proyecto, agentes, modelos
var roleCognitiveServicesUser = 'a97b65f3-24c7-4388-baec-2e87135dc908' // Content Safety (Prompt Shields)
var roleAcrPull = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

// ---------------------------------------------------------------- Observabilidad
resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'rm-logs-${token}'
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'rm-appi-${token}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logs.id
  }
}

// ---------------------------------------------------------------- Microsoft Foundry
resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: foundryName
  location: location
  tags: tags
  kind: 'AIServices'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    allowProjectManagement: true
    customSubDomainName: foundryName
    disableLocalAuth: true // solo Entra ID: nada de keys
    publicNetworkAccess: 'Enabled'
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: foundry
  name: projectName
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    displayName: 'Readymind · AI Tour México'
    description: 'Demo del stand: enjambre de agentes con Microsoft Agent Framework'
  }
}

// Guardrail del stand: filtros de contenido + Prompt Shields (ataques directos e indirectos) bloqueando.
// Las operaciones sobre la cuenta van en serie (proyecto → guardrail → deployments → conexión): en paralelo ARM
// responde RequestConflict ("Another operation is in progress").
resource guardrail 'Microsoft.CognitiveServices/accounts/raiPolicies@2025-06-01' = {
  parent: foundry
  name: guardrailName
  dependsOn: [project]
  properties: {
    basePolicyName: 'Microsoft.DefaultV2'
    mode: 'Blocking'
    contentFilters: [
      { name: 'Hate', blocking: true, enabled: true, severityThreshold: 'Medium', source: 'Prompt' }
      { name: 'Hate', blocking: true, enabled: true, severityThreshold: 'Medium', source: 'Completion' }
      { name: 'Sexual', blocking: true, enabled: true, severityThreshold: 'Medium', source: 'Prompt' }
      { name: 'Sexual', blocking: true, enabled: true, severityThreshold: 'Medium', source: 'Completion' }
      { name: 'Violence', blocking: true, enabled: true, severityThreshold: 'Medium', source: 'Prompt' }
      { name: 'Violence', blocking: true, enabled: true, severityThreshold: 'Medium', source: 'Completion' }
      { name: 'Selfharm', blocking: true, enabled: true, severityThreshold: 'Medium', source: 'Prompt' }
      { name: 'Selfharm', blocking: true, enabled: true, severityThreshold: 'Medium', source: 'Completion' }
      { name: 'Jailbreak', blocking: true, enabled: true, source: 'Prompt' }
      { name: 'Indirect Attack', blocking: true, enabled: true, source: 'Prompt' }
      { name: 'Protected Material Text', blocking: true, enabled: true, source: 'Completion' }
    ]
  }
}

@batchSize(1) // los deployments de una misma cuenta se crean de a uno
resource deployments 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = [for d in modelDeployments: {
  parent: foundry
  name: d.name
  sku: {
    name: d.?sku ?? 'GlobalStandard'
    capacity: d.?capacity ?? 50
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: d.model
      version: d.version
    }
    raiPolicyName: guardrail.name
  }
}]

// App Insights conectado al proyecto: las trazas aparecen en Tracing de Foundry.
resource appInsightsConnection 'Microsoft.CognitiveServices/accounts/connections@2025-06-01' = {
  parent: foundry
  name: 'appinsights'
  dependsOn: [deployments]
  properties: {
    category: 'AppInsights'
    target: appInsights.id
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: { key: appInsights.properties.ConnectionString }
    metadata: {
      ApiType: 'Azure'
      ResourceId: appInsights.id
    }
  }
}

// ---------------------------------------------------------------- Identidad de la app
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'rm-id-${token}'
  location: location
  tags: tags
}

resource appFoundryRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: foundry
  name: guid(foundry.id, identity.id, roleAzureAIUser)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleAzureAIUser)
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource appSafetyRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: foundry
  name: guid(foundry.id, identity.id, roleCognitiveServicesUser)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleCognitiveServicesUser)
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Quien corre azd también puede usar el proyecto (desarrollo local y scripts como create_voice_agent).
resource userFoundryRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  scope: foundry
  name: guid(foundry.id, principalId, roleAzureAIUser)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleAzureAIUser)
    principalId: principalId
    principalType: 'User'
  }
}

resource userSafetyRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  scope: foundry
  name: guid(foundry.id, principalId, roleCognitiveServicesUser)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleCognitiveServicesUser)
    principalId: principalId
    principalType: 'User'
  }
}

// ---------------------------------------------------------------- Imagen
resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: 'rmacr${token}'
  location: location
  tags: tags
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: false }
}

resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: registry
  name: guid(registry.id, identity.id, roleAcrPull)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleAcrPull)
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ---------------------------------------------------------------- Almacenamiento de /data (one-pagers, PDFs, leads, grabaciones)
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: 'rmst${token}'
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
  }
}

resource fileService 'Microsoft.Storage/storageAccounts/fileServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource share 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-05-01' = {
  parent: fileService
  name: 'data'
  properties: { shareQuota: 20 }
}

// ---------------------------------------------------------------- Container Apps
resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'rm-env-${token}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

resource envStorage 'Microsoft.App/managedEnvironments/storages@2024-03-01' = {
  parent: env
  name: 'data'
  properties: {
    azureFile: {
      accountName: storage.name
      accountKey: storage.listKeys().keys[0].value
      shareName: share.name
      accessMode: 'ReadWrite'
    }
  }
}

var projectEndpoint = 'https://${foundryName}.services.ai.azure.com/api/projects/${projectName}'
var accountEndpoint = 'https://${foundryName}.cognitiveservices.azure.com/'
var publicUrl = 'https://${appName}.${env.properties.defaultDomain}'

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  tags: union(tags, { 'azd-service-name': 'web' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identity.id}': {} }
  }
  dependsOn: [acrPull]
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto' // HTTP + WebSockets (pantalla y voz)
        allowInsecure: false
      }
      registries: [{ server: registry.properties.loginServer, identity: identity.id }]
      secrets: [
        { name: 'lead-secret', value: leadSecret }
        { name: 'power-automate-url', value: empty(powerAutomateUrl) ? 'none' : powerAutomateUrl }
      ]
    }
    template: {
      containers: [
        {
          name: 'web'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // azd deploy la reemplaza
          resources: { cpu: json('2.0'), memory: '4Gi' } // Chromium para el PDF
          env: [
            { name: 'DEMO_MODE', value: 'live' }
            { name: 'AZURE_CLIENT_ID', value: identity.properties.clientId } // DefaultAzureCredential → Managed Identity
            { name: 'FOUNDRY_PROJECT_ENDPOINT', value: projectEndpoint }
            { name: 'CONTENT_SAFETY_ENDPOINT', value: accountEndpoint }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
            { name: 'MODEL_ARQUITECTO', value: modelArquitecto }
            { name: 'MODEL_FINANCIERO', value: modelFinanciero }
            { name: 'MODEL_RIESGO', value: modelRiesgo }
            { name: 'MODEL_DIAGRAMADOR', value: modelDiagramador }
            { name: 'MODEL_REDACTOR', value: modelRedactor }
            { name: 'MODEL_GUARD', value: modelGuard }
            { name: 'VOICE_RAI_POLICY', value: guardrail.id } // el voice agent exige el ID ARM completo
            { name: 'PUBLIC_BASE_URL', value: publicUrl }
            { name: 'LEAD_SECRET', secretRef: 'lead-secret' }
            { name: 'POWER_AUTOMATE_URL', secretRef: 'power-automate-url' }
            { name: 'DATA_DIR', value: '/data' }
            { name: 'RECORDINGS_DIR', value: '/data/recordings' }
          ]
          volumeMounts: [{ volumeName: 'data', mountPath: '/data' }]
        }
      ]
      volumes: [{ name: 'data', storageType: 'AzureFile', storageName: envStorage.name }]
      // UNA réplica siempre encendida: la sesión del stand y el bus viven en memoria y no hay arranque en frío.
      scale: { minReplicas: 1, maxReplicas: 1 }
    }
  }
}

output registryLoginServer string = registry.properties.loginServer
output projectEndpoint string = projectEndpoint
output accountEndpoint string = accountEndpoint
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output publicUrl string = publicUrl
output guardrailId string = guardrail.id
