// Readymind · Microsoft AI Tour México — infraestructura del stand (azd up).
// Crea el grupo de recursos y delega todo en resources.bicep.
targetScope = 'subscription'

@minLength(1)
@maxLength(40)
@description('Nombre del entorno de azd (se usa para nombrar recursos).')
param environmentName string

@description('Región. Debe soportar Agent Service, voice agents (preview) y los modelos elegidos (ej. eastus2, swedencentral).')
param location string = 'eastus2'

@description('Object ID de quien corre azd: recibe permisos para usar el proyecto desde su máquina (vacío = ninguno).')
param principalId string = ''

@description('Deployments de modelos. Confirmar nombre/versión/capacidad disponibles en el catálogo de Foundry de la región.')
param modelDeployments array = []

@secure()
@description('Firma de los links del QR. Se genera sola si no se indica.')
param leadSecret string = newGuid()

@secure()
@description('URL del disparador HTTP de Power Automate que envía el correo (vacío = los leads quedan en outbox).')
param powerAutomateUrl string = ''

param modelArquitecto string = 'gpt-5.4'
param modelFinanciero string = 'gpt-5.4-mini'
param modelRiesgo string = 'gpt-5.4-mini'
param modelRedactor string = 'gpt-5.4-mini'
param modelGuard string = 'gpt-5.4-nano'

var tags = { 'azd-env-name': environmentName, proyecto: 'readymind-aitour' }

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

module resources 'resources.bicep' = {
  name: 'resources'
  scope: rg
  params: {
    environmentName: environmentName
    location: location
    tags: tags
    principalId: principalId
    modelDeployments: modelDeployments
    leadSecret: leadSecret
    powerAutomateUrl: powerAutomateUrl
    modelArquitecto: modelArquitecto
    modelFinanciero: modelFinanciero
    modelRiesgo: modelRiesgo
    modelRedactor: modelRedactor
    modelGuard: modelGuard
  }
}

output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = resources.outputs.registryLoginServer
output FOUNDRY_PROJECT_ENDPOINT string = resources.outputs.projectEndpoint
output CONTENT_SAFETY_ENDPOINT string = resources.outputs.accountEndpoint
output APPLICATIONINSIGHTS_CONNECTION_STRING string = resources.outputs.appInsightsConnectionString
output PUBLIC_BASE_URL string = resources.outputs.publicUrl
output VOICE_RAI_POLICY string = resources.outputs.guardrailName
