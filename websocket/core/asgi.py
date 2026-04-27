"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

# 1. Set the settings first
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# 2. Initialize Django BEFORE importing any local apps/routing
django.setup()

# 3. NOW it is safe to import your local routing
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from notifications.routing import websocket_urlpatterns as notif_urls
from chat.routing import websocket_urlpatterns as chat_urls

from channels.security.websocket import AllowedHostsOriginValidator

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                chat_urls + notif_urls
            )
        ),
    }
)


# ProtocolTypeRouterRoutes incoming connection to the right handler based on protocol (HTTP or WebSocket)

# get_asgi_application()Handles normal HTTP requests — same as before


# AuthMiddlewareStackAttaches the logged-in user to the WebSocket connection so consumers know who's connecting

# URLRouterRoutes WebSocket connections by URL path — like urls.py but for WebSocket
