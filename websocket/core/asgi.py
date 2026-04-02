"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
# from notifications.routing import websocket_urlpatterns as notif_urls
from notifications.routing import websocket_urlpatterns as notif_urls

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
from chat.routing import websocket_urlpatterns as chat_urls
application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                chat_urls + notif_urls
                # routes will be added here as we build each consumer
                # just like urls
                # in here i want to understand some more thigns
            )
        ),
    }
)


# ProtocolTypeRouterRoutes incoming connection to the right handler based on protocol (HTTP or WebSocket)

# get_asgi_application()Handles normal HTTP requests — same as before


# AuthMiddlewareStackAttaches the logged-in user to the WebSocket connection so consumers know who's connecting

# URLRouterRoutes WebSocket connections by URL path — like urls.py but for WebSocket
