from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.core.cache import cache
from django.utils import timezone
from django.contrib.sessions.models import Session
from asgiref.sync import sync_to_async

class SessionExpirationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if user.is_authenticated:
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get("check_session") == True:
            user = self.scope.get('user')

            if user.is_authenticated:
                # Obtenemos la clave de la sesión
                session_key = self.scope["session"].session_key
                
                # Verificamos si la hora de expiración está en caché
                session_expiry = cache.get(f"session_expiry_{session_key}")

                if session_expiry is None:
                    # Si no está en caché, obtenemos la hora de expiración de la base de datos
                    session_expiry = await self.get_session_expiry(session_key)
                    # Almacenamos la expiración en caché para futuras consultas
                    cache.set(f"session_expiry_{session_key}", session_expiry, timeout=300)  # Timeout de 5 minutos

                # Comprobamos si la sesión ha expirado
                if session_expiry <= timezone.now():
                    await self.send(text_data=json.dumps({
                        'status': 'session_expired',
                    }))
                else:
                    await self.send(text_data=json.dumps({
                        'status': 'session_active',
                    }))
            else:
                await self.send(text_data=json.dumps({
                    'status': 'session_inactive',
                }))

    # Envolver la consulta al ORM con sync_to_async
    @sync_to_async
    def get_session_expiry(self, session_key):
        try:
            session = Session.objects.get(session_key=session_key)
            return session.expire_date  # Usar 'expire_date' en lugar de 'get_expiry_date'
        except Session.DoesNotExist:
            return timezone.now()  # Si no existe la sesión, consideramos la expiración como ahora
