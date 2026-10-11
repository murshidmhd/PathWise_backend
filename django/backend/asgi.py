import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from chat.routing import websocket_urlpatterns as chat_urls
from notifications.routing import websocket_urlpatterns as notif_urls
from simulations.routing import websocket_urlpatterns as sim_urls

@database_sync_to_async
def get_tenant_by_host(host):
    from django_tenants.utils import get_tenant_model
    TenantModel = get_tenant_model()
    try:
        return TenantModel.objects.get(domains__domain=host)
    except TenantModel.DoesNotExist:
        return None

# Custom middleware to handle subdomains in WebSockets
class TenantAwareMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        from django_tenants.utils import remove_www
        
        hostname = None
        for header in scope.get("headers", []):
            if header[0] == b"host":
                hostname = remove_www(header[1].decode("utf-8").split(":")[0])
                break
        
        if hostname:
            tenant = await get_tenant_by_host(hostname)
            if tenant:
                scope["tenant"] = tenant
                
        return await self.inner(scope, receive, send)

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TenantAwareMiddleware(
        AuthMiddlewareStack(
            URLRouter(
                chat_urls + notif_urls + sim_urls
            )
        )
    ),
})
