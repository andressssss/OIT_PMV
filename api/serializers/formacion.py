from rest_framework import serializers
from commons.models import T_raps, T_compe, T_ficha, T_fase, T_fase_ficha
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

class FichaEditarSerializer(FichaSerializer):
    fase_id = serializers.SerializerMethodField()
    muni_id = serializers.SerializerMethodField()
    depa_id = serializers.SerializerMethodField()

    class Meta:
        model = T_ficha
        fields = FichaSerializer.Meta.fields + ['centro_id', 'insti_id', 'progra_id', 'fase_id', 'muni_id', 'depa_id']

    def get_fase_id(self, ficha):
        fase_actual = T_fase_ficha.objects.filter(ficha=ficha, vige=1).first()
        return fase_actual.fase_id if fase_actual else None
    
    def get_muni_id(self, ficha):
        if ficha.insti and ficha.insti.muni:
            return ficha.insti.muni.id
        return None
    
    def get_depa_id(self, ficha):
        if ficha.insti and ficha.insti.muni and ficha.insti.muni.nom_departa:
            return ficha.insti.muni.nom_departa.id
        return None
    
    def validate_num(self, value):
        if value:
            ficha_id = self.instance.id if self.instance else None
            if T_ficha.objects.exclude(id=ficha_id).filter(num=value).exists():
                raise serializers.ValidationError("Ya existe una ficha con este número.")
        return value

        
    def update(self, instance, validated_data):
        instance.num = validated_data.get('num', instance.num)
        instance.insti_id = validated_data.get('insti_id', instance.insti_id)
        instance.centro_id = validated_data.get('centro_id', instance.centro_id)
        instance.progra_id = validated_data.get('progra_id', instance.progra_id)

        fase_id = self.context['request'].data.get('fase_id')
        if fase_id:
            T_fase_ficha.objects.filter(ficha=instance, vige=1).update(fase_id=fase_id)

        instance.save()
        return instance


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

class ProgramaSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_raps
        fields = ['id', 'nom']