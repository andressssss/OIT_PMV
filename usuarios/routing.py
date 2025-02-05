from django.urls import path
from .consumers import SessionExpirationConsumer

websocket_urlpatterns = [
    path('ws/session_expiration/', SessionExpirationConsumer.as_asgi()),
]

