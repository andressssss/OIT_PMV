from rest_framework import serializers
from commons.models import T_perfil

class PerfilSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source='user.username', read_only=True)
    last_login = serializers.DateTimeField(source='user.last_login', read_only=True)

    class Meta:
        model = T_perfil
        fields = [
            'id',
            'username',
            'last_login',
            'nom',
            'apelli',
            'tipo_dni',
            'dni',
            'tele',
            'dire',
            'mail',
            'gene',
            'fecha_naci',
            'rol'
        ]