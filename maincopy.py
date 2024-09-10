import pulumi
from pulumi_azure_native import network, cache, web, dbforpostgresql, managedidentity, resources
from pulumi import Output
from django.core.management.utils import get_random_secret_key

# Definindo variáveis básicas
resource_group_name = "cookiecutter-pulumi-django_group"
location_brazilsouth = "brazilsouth"
location_global = "global"
secret_key = get_random_secret_key()

# Criando o Resource Group com nome fixo
resource_group = resources.ResourceGroup(
    "resource_group",
    resource_group_name=resource_group_name,
    location=location_brazilsouth
)

# Criando Virtual Network com nome fixo
vnet = network.VirtualNetwork(
    "vnet",
    name="cookiecutter-pulumi-django-vnet",  # Nome fixo
    resource_group_name=resource_group.name,
    location=resource_group.location,
    address_space=network.AddressSpaceArgs(
        address_prefixes=["10.0.0.0/16"]
    )
)

# Criando Subnet para PostgreSQL e Redis com nome fixo
subnet = network.Subnet(
    "subnet",
    name="cookiecutter-pulumi-django-subnet",  # Nome fixo
    resource_group_name=resource_group.name,
    virtual_network_name=vnet.name,
    address_prefix="10.0.1.0/24"
)

# Criando Subnet para PostgreSQL com delegação para PostgreSQL
subnet_postgres = network.Subnet(
    "subnet_postgres",
    name="cookiecutter-pulumi-django-subnet-postgres",  # Nome fixo para subnet do PostgreSQL
    resource_group_name=resource_group.name,
    virtual_network_name=vnet.name,
    address_prefix="10.0.2.0/24",
    delegations=[network.DelegationArgs(
        name="dbforpostgresqldelegation",
        service_name="Microsoft.DBforPostgreSQL/flexibleServers"
    )]  # Delegação para o serviço de PostgreSQL
)

# Criando Private DNS Zone para Redis com nome fixo
private_dns_redis = network.PrivateZone(
    "private_dns_redis",
    name="privatelink.redis.cache.windows.net",  # Nome fixo
    resource_group_name=resource_group.name,
    location=location_global
)

# Criando Private DNS Zone para PostgreSQL com nome fixo
private_dns_postgres = network.PrivateZone(
    "private_dns_postgres",
    name="privatelink.postgres.database.azure.com",  # Nome fixo
    resource_group_name=resource_group.name,
    location=location_global
)

# Criando Redis Cache com nome fixo
redis_cache = cache.Redis(
    "redis_cache",
    name="cookiecutter-pulumi-django-cache",  # Nome fixo
    resource_group_name=resource_group.name,
    location=resource_group.location,
    sku=cache.SkuArgs(
        name="Standard",
        family="C",
        capacity=1
    )
)

# Criando Private Endpoint para Redis Cache com nome fixo
private_endpoint_redis = network.PrivateEndpoint(
    "private_endpoint_redis",
    name="cookiecutter-pulumi-django-cache-privateEndpoint",  # Nome fixo
    resource_group_name=resource_group.name,
    location=resource_group.location,
    private_link_service_connections=[network.PrivateLinkServiceConnectionArgs(
        name="redisConnection",
        private_link_service_id=redis_cache.id,
        group_ids=["redisCache"]
    )],
    subnet=network.SubnetArgs(
        id=subnet.id
    )
)

# Criando Virtual Network Link para Redis DNS com nome fixo
vnet_link_redis = network.VirtualNetworkLink(
    "vnet_link_redis",
    name="privatelink.redis.cache.windows.net-applink",  # Nome fixo
    resource_group_name=resource_group.name,
    location=location_global,
    private_zone_name=private_dns_redis.name,
    virtual_network=network.SubResourceArgs(
        id=vnet.id
    ),
    registration_enabled=False
)

# Criando PostgreSQL Server com nome fixo
postgres_server = dbforpostgresql.Server(
    "postgres_server",
    name="cookiecutter-pulumi-django-server",  # Nome fixo
    resource_group_name=resource_group.name,
    location=location_brazilsouth,
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
        delegated_subnet_resource_id=subnet.id,
        private_dns_zone_arm_resource_id=private_dns_postgres.id  # Usando o ID da Private DNS Zone criada
    )
)

# Criando Virtual Network Link para PostgreSQL DNS com nome fixo
vnet_link_postgres = network.VirtualNetworkLink(
    "vnet_link_postgres",
    name="privatelink.postgres.database.azure.com-dblink",  # Nome fixo
    resource_group_name=resource_group.name,
    location=location_global,
    private_zone_name=private_dns_postgres.name,
    virtual_network=network.SubResourceArgs(
        id=vnet.id
    ),
    registration_enabled=False
)

# Criando App Service Plan com nome fixo
app_service_plan = web.AppServicePlan(
    "app_service_plan",
    name="ASP-cookiecutterpulumi123group",  # Nome fixo
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

# Criando o App Service para hospedar a aplicação Django com nome fixo
app_service = web.WebApp(
    "app_service",
    name="cookiecutter-pulumi-django",  # Nome fixo
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
    virtual_network_subnet_id=subnet.id,
    location=resource_group.location
)

# Criando Managed Identity com nome fixo
managed_identity = managedidentity.UserAssignedIdentity(
    "managed_identity",
    name="cookiecutter-pul-id",  # Nome fixo
    resource_group_name=resource_group.name,
    location=resource_group.location
)

# Exportando saídas
pulumi.export("resource_group_name", resource_group.name)
pulumi.export("redis_cache_name", redis_cache.name)
pulumi.export("postgresql_server_name", postgres_server.name)
pulumi.export("web_app_url", app_service.default_host_name)
pulumi.export("managed_identity_name", managed_identity.name)
