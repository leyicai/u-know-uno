from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import unoGame.routing
import gameTables.routing
from django.urls import path

ASGI_APPLICATION = "UKnowUNO.routing.application"
application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(
            unoGame.routing.websocket_urlpatterns +
            gameTables.routing.websocket_urlpatterns
        )
    ),
})
