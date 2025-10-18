from commons.models import T_nove
from rest_framework import serializers

class NovedadFiltrarSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_nove
        fields = ["id"]