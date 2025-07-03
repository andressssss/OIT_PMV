from rest_framework import serializers
from commons.models import T_raps, T_compe, T_ficha, T_fase
import logging

logger = logging.getLogger(__name__)


# Serializers reutilizables
class CompetenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_compe
        fields = ['id', 'nom']


class FichaSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_ficha
        fields = ['id', 'num']


# Serializer base compartido entre Create y Update
class BaseRapsSerializer(serializers.ModelSerializer):
    compe = serializers.PrimaryKeyRelatedField(
        queryset=T_compe.objects.all()
    )
    fase = serializers.PrimaryKeyRelatedField(
        queryset=T_fase.objects.all(), many=True
    )

    class Meta:
        model = T_raps
        fields = ['nom', 'compe', 'fase']

    def validate_nom(self, value):
        qs = T_raps.objects.filter(nom=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError("Ya existe un RAP con ese nombre")
        return value

    def create(self, validated_data):
        fases = validated_data.pop('fase', [])
        validated_data['comple'] = "No"
        rap = T_raps.objects.create(**validated_data)
        rap.fase.set(fases)
        logger.warning(f"[CREATE RAP] Fases asociadas: {fases}")
        return rap

    def update(self, instance, validated_data):
        fases = validated_data.pop('fase', None)

        instance.nom = validated_data.get('nom', instance.nom)
        instance.compe = validated_data.get('compe', instance.compe)
        instance.save()

        if fases is not None:
            logger.warning(f"[PATCH RAP] Fases a asociar: {fases}")
            instance.fase.set(fases)
            logger.warning(f"[PATCH RAP] Fases asociadas: {[f.id for f in instance.fase.all()]}")
        return instance

# Serializer para lectura (GET)
class RAPSerializer(serializers.ModelSerializer):
    compe = serializers.PrimaryKeyRelatedField(queryset=T_compe.objects.all())
    programas = serializers.SerializerMethodField()
    fase = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )

    class Meta:
        model = T_raps
        fields = ['id', 'nom', 'compe', 'programas', 'fase']

    def get_programas(self, obj):
        programas = obj.compe.progra.all()
        return [{'id': p.id, 'nom': p.nom} for p in programas]
