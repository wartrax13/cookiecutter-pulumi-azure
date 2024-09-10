import pulumi
import os
from pulumi_azure_native import network, cache, web, dbforpostgresql, managedidentity, resources
from pulumi import Output

# az resource list --resource-group django-azure-pulumi-123_group --output table
# az resource show --ids "/subscriptions/SUBSCRIPTION_ID/resourceGroups/RESOURCE_GROUP" output table
# Subscription ID e Resource Group

# Definindo variáveis básicas
resource_group_name = "cookiecutter-pulumi-django_group"
location_brazilsouth = "brazilsouth"
location_global = "global"
secret_key = os.getenv('SECRET_KEY')

# Criando o Resource Group
resource_group = resources.ResourceGroup(
    resource_group_name,
    location=location_brazilsouth
)

# Criando Virtual Network
vnet = network.VirtualNetwork(
    "cookiecutter-pulumi-djangoVnet",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    address_space=network.AddressSpaceArgs(
        address_prefixes=["10.0.0.0/16"]
    )
)

# Criando Subnet para PostgreSQL e Redis
subnet_main = network.Subnet(
    "cookiecutter-pulumi-django-subnet",
    resource_group_name=resource_group.name,
    virtual_network_name=vnet.name,
    address_prefix="10.0.1.0/24"
)

# Criando Subnet para PostgreSQL com delegação para PostgreSQL
subnet_postgres = network.Subnet(
    "cookiecutter-pulumi-django-subnet-postgres",
    resource_group_name=resource_group.name,
    virtual_network_name=vnet.name,
    address_prefix="10.0.2.0/24",
    delegations=[
        network.DelegationArgs(
        name="dbforpostgresqldelegation",
        service_name="Microsoft.DBforPostgreSQL/flexibleServers"
    )]
)

subnet_app = network.Subnet(
    "cookiecutter-pulumi-django-subnet-app",
    resource_group_name=resource_group.name,
    virtual_network_name=vnet.name,
    address_prefix="10.0.3.0/24",
    delegations=[network.DelegationArgs(
        name="appservicedelegation",
        service_name="Microsoft.Web/serverFarms"
    )]
)

# Criando Private DNS Zone para Redis
private_dns_redis = network.PrivateZone(
    "privatelink.redis.cache.windows.net",
    resource_group_name=resource_group.name,
    location=location_global,
    private_zone_name="privatelink.redis.cache.windows.net"
)

# Criando Private DNS Zone para PostgreSQL
private_dns_postgres = network.PrivateZone(
    "privatelink.postgres.database.azure.com",
    resource_group_name=resource_group.name,
    location=location_global,
    private_zone_name="privatelink.postgres.database.azure.com"
)


# Criando Redis Cache
redis_cache = cache.Redis(
    "cookiecutter-pulumi-django-cache",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    sku=cache.SkuArgs(
        name="Standard",
        family="C",
        capacity=1
    )
)

# Criando Private Endpoint para Redis Cache
private_endpoint_redis = network.PrivateEndpoint(
    "cookiecutter-pulumi-django-cache-privateEndpoint",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    private_link_service_connections=[network.PrivateLinkServiceConnectionArgs(
        name="redisConnection",
        private_link_service_id=redis_cache.id,
        group_ids=["redisCache"]
    )],
    subnet=network.SubnetArgs(
        id=subnet_main.id
    )
)

# Criando Virtual Network Link para Redis DNS
vnet_link_redis = network.VirtualNetworkLink(
    "privatelink.redis.cache.windows.net-applink",
    resource_group_name=resource_group.name,
    location=location_global,
    private_zone_name=private_dns_redis.name,
    virtual_network=network.SubResourceArgs(
        id=vnet.id
    ),
    registration_enabled=False
)

# PostgreSQL Server
postgres_server = dbforpostgresql.Server(
    "cookiecutter-pulumi-django-server",
    resource_group_name=resource_group.name,
    location="brazilsouth",
    sku=dbforpostgresql.SkuArgs(
        name="Standard_B2ms",
        tier="Burstable",
    ),
    version=dbforpostgresql.ServerVersion.SERVER_VERSION_12,
    administrator_login="admin_user",
    administrator_login_password="Admin@123",
    auth_config=dbforpostgresql.AuthConfigArgs(
        password_auth=dbforpostgresql.PasswordAuthEnum.DISABLED,
        active_directory_auth=dbforpostgresql.ActiveDirectoryAuthEnum.ENABLED,
    ),
    storage=dbforpostgresql.StorageArgs(storage_size_gb=32),
    backup=dbforpostgresql.BackupArgs(
        backup_retention_days=7,
        geo_redundant_backup=dbforpostgresql.GeoRedundantBackupEnum.DISABLED,
    ),
    network=dbforpostgresql.NetworkArgs(
        delegated_subnet_resource_id=subnet_postgres.id,
        private_dns_zone_arm_resource_id=private_dns_postgres.id  # Usando o ID da Private DNS Zone criada
    )
)

# Criando Virtual Network Link para PostgreSQL DNS
vnet_link_postgres = network.VirtualNetworkLink(
    "privatelink.postgres.database.azure.com-dblink",
    resource_group_name=resource_group.name,
    location=location_global,
    private_zone_name=private_dns_postgres.name,
    virtual_network=network.SubResourceArgs(
        id=vnet.id
    ),
    registration_enabled=False
)

# Criando App Service Plan
app_service_plan = web.AppServicePlan(
    "ASP-cookiecutterpulumi123group",
    resource_group_name=resource_group.name,
    location=resource_group.location,
    kind="linux",
    reserved=True,
    sku=web.SkuDescriptionArgs(
        name="B1",
        tier="Basic",
        capacity=1
    )
)

# Criar o App Service para hospedar a aplicação Django
app_service = web.WebApp(
    "cookiecutter-pulumi-django",
    resource_group_name=resource_group.name,
    server_farm_id=app_service_plan.id,
    site_config=web.SiteConfigArgs(
        linux_fx_version="PYTHON|3.10",
        app_settings=[
            web.NameValuePairArgs(name="POSTGRES_DB", value='postgres'),
            web.NameValuePairArgs(name="POSTGRES_USER", value="admin_user"),
            web.NameValuePairArgs(name="POSTGRES_PASSWORD", value="Admin@123"),
            web.NameValuePairArgs(name="POSTGRES_HOST", value=Output.concat(postgres_server.name, ".postgres.database.azure.com")),
            web.NameValuePairArgs(name="DJANGO_SETTINGS_MODULE", value="core.settings"),
            web.NameValuePairArgs(name="REDIS_URL", value=Output.concat("redis://", redis_cache.host_name, ":6379")),
            web.NameValuePairArgs(name="SECRET_KEY", value=secret_key),
        ],
    ),
    vnet_route_all_enabled=True,
    virtual_network_subnet_id=subnet_app.id,
    location=resource_group.location
)

# Criando Managed Identity
managed_identity = managedidentity.UserAssignedIdentity(
    "cookiecutter-pul-id",
    resource_group_name=resource_group.name,
    location=resource_group.location
)

# Exportando saídas
pulumi.export("resource_group_name", resource_group.name)
pulumi.export("redis_cache_name", redis_cache.name)
pulumi.export("postgresql_server_name", postgres_server.name)
pulumi.export("web_app_url", app_service.default_host_name)
pulumi.export("managed_identity_name", managed_identity.name)
