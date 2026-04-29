from rest_framework import serializers
from tasks.models import T_notifi


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_notifi
        fields = (
            'id', 'titulo', 'mensaje', 'nivel', 'url',
            'leida', 'leida_en', 'creada_en',
            'origen_tipo', 'origen_id',
        )
        read_only_fields = fields
