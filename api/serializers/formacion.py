from rest_framework import serializers
from commons.models import T_raps, T_compe, T_ficha

class RAPSerializer(serializers.ModelSerializer):
    compe = serializers.PrimaryKeyRelatedField(queryset=T_compe.objects.all())
    programas = serializers.SerializerMethodField()
    
    class Meta:
        model = T_raps
        fields = ['id', 'nom', 'compe', 'programas']

    def get_programas(self, obj):
        programas = obj.compe.progra.all()
        return [{'id': p.id, 'nom': p.nom} for p in programas]

class RapsCreateSerializer(serializers.ModelSerializer):
    compe = serializers.PrimaryKeyRelatedField(
        queryset=T_compe.objects.all(), write_only=True
    )

    class Meta:
        model = T_raps
        fields = ['nom', 'compe']

    def validate_nom(self, value):
        if T_raps.objects.filter(nom=value).exists():
            raise serializers.ValidationError("Ya existe un RAP con ese nombre")
        return value

    def create(self, validated_data):
        validated_data['comple'] = "No"
        return T_raps.objects.create(**validated_data)

class CompetenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_compe
        fields = ['id', 'nom']

class FichaSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_ficha
        fields = ['id', 'num']