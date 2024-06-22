import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.layers import get_channel_layer

from app.routing import websocket_urlpatterns

print("ZD",websocket_urlpatterns)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DendyTanksBackend.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
})

channel_layer = get_channel_layer()
