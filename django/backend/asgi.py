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

# Custom middleware to handle subdomains in WebSockets
class TenantAwareMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        from django_tenants.utils import get_tenant_model, remove_www
        from django.db import connection
        
        hostname = None
        for header in scope.get("headers", []):
            if header[0] == b"host":
                hostname = remove_www(header[1].decode("utf-8").split(":")[0])
                break
        
        if hostname:
            TenantModel = get_tenant_model()
            try:
                @database_sync_to_async
                def get_tenant(host):
                    return TenantModel.objects.get(domains__domain=host)
                
                tenant = await get_tenant(hostname)
                connection.set_tenant(tenant)
            except Exception:
                pass
                
        return await self.inner(scope, receive, send)

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TenantAwareMiddleware(
        AuthMiddlewareStack(
            URLRouter(
                chat_urls + notif_urls
            )
        )
    ),
})
