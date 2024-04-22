echo ""
echo "Loading azd .env file from current environment.."
echo ""

while IFS='=' read -r key value; do
    value=$(echo "$value" | sed 's/^"//' | sed 's/"$//')
    export "$key=$value"
    echo "export $key=$value"
done <<EOF
$(azd env get-values)
EOF

if [ $? -ne 0 ]; then
    echo "Failed to load environment variables from azd environment"
    exit $?
fi

echo ""
echo "Setting up service principal for local Docker use.."
echo ""

roles=(
    "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd"
)

displayName="openai-chat-backend-fastapi-docker"
export servicePrincipal=$(az ad sp list --display-name $displayName --query [].appId --output tsv)

if [ -z "$servicePrincipal" ]; then
    echo "Service principal not found. Creating service principal..."
    export servicePrincipal=$(az ad sp create-for-rbac --name $displayName --role reader --scopes /subscriptions/"$AZURE_SUBSCRIPTION_ID"/resourceGroups/"$AZURE_RESOURCE_GROUP" --query appId --output tsv)
    if [ $? -ne 0 ]; then
        echo "Failed to create service principal"
        exit $?
    fi
    export servicePrincipalObjectId=$(az ad sp show --id "$servicePrincipal" --query id --output tsv)
    echo "Assigning Roles to service principal $displayName with principal id:$servicePrincipal and object id[$servicePrincipalObjectId]"
    for role in "${roles[@]}"; do

        echo "Assigning Role[$role] to principal id[$servicePrincipal] for resource[/subscriptions/"$AZURE_SUBSCRIPTION_ID"/resourceGroups/"$AZURE_RESOURCE_GROUP"] "
        az role assignment create \
            --role "$role" \
            --assignee-object-id "$servicePrincipalObjectId" \
            --scope /subscriptions/"$AZURE_SUBSCRIPTION_ID"/resourceGroups/"$AZURE_RESOURCE_GROUP" \
            --assignee-principal-type ServicePrincipal
    done
    fi

echo "Getting service principal credentials"
export servicePrincipalPassword=$(az ad sp credential reset --id "$servicePrincipal"  --query password --output tsv)
export servicePrincipalTenant=$(az ad sp show --id "$servicePrincipal" --query appOwnerOrganizationId --output tsv)

echo ""
echo "Starting solution locally using docker compose. "
echo ""

docker compose -f ./docker-compose.yaml up
