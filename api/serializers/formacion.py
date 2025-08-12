from rest_framework import serializers
from commons.models import T_raps, T_compe, T_ficha, T_fase, T_fase_ficha, T_insti_edu, T_centro_forma
import logging

logger = logging.getLogger(__name__)


# Serializers reutilizables
class CompetenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_compe
        fields = ['id', 'nom']


class CompetenciaWriteSerializer(CompetenciaSerializer):
    progra = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )

    class Meta(CompetenciaSerializer.Meta):
        fields = CompetenciaSerializer.Meta.fields + ['cod', 'progra']

    def validate_nom(self, value):
        qs = T_compe.objects.filter(nom__iexact=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Ya existe una competencia con este nombre.")
        return value

    def create(self, validated_data):
        programas_ids = validated_data.pop('progra', [])
        competencia = T_compe.objects.create(**validated_data)
        competencia.progra.set(programas_ids)
        return competencia

    def update(self, instance, validated_data):
        programas_ids = validated_data.pop('progra', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if programas_ids is not None:
            instance.progra.set(programas_ids)
        return instance


class CompetenciaDetalleSerializer(CompetenciaSerializer):
    progra = serializers.SerializerMethodField()

    class Meta(CompetenciaSerializer.Meta):
        fields = CompetenciaSerializer.Meta.fields + ['cod', 'progra']

    def get_progra(self, obj):
        return list(obj.progra.values_list('id', flat=True))


class CompetenciaTablaSerializer(CompetenciaSerializer):
    progra = serializers.SerializerMethodField()

    class Meta(CompetenciaSerializer.Meta):
        fields = CompetenciaSerializer.Meta.fields + ['cod', 'progra']

    def get_progra(self, obj):
        return [p.nom for p in obj.progra.all()]


class FichaSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_ficha
        fields = ['id', 'num']


class FichaEditarSerializer(FichaSerializer):

    insti_id = serializers.PrimaryKeyRelatedField(
        queryset=T_insti_edu.objects.all(), required=False)
    centro_id = serializers.PrimaryKeyRelatedField(
        queryset=T_centro_forma.objects.all(), required=False)

    fase_id = serializers.SerializerMethodField()
    muni_id = serializers.SerializerMethodField()
    depa_id = serializers.SerializerMethodField()

    class Meta:
        model = T_ficha
        fields = FichaSerializer.Meta.fields + \
            ['centro_id', 'insti_id', 'progra_id', 'fase_id', 'muni_id', 'depa_id']

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
                raise serializers.ValidationError(
                    "Ya existe una ficha con este número.")
        return value

    def update(self, instance, validated_data):
        logger.warning(f"Mensaje to wapo")
        logger.warning(f"{self.context['request'].data}")

        instance.num = validated_data.get('num', instance.num)
        instance.insti = validated_data.get('insti_id', instance.insti)
        instance.centro = validated_data.get('centro_id', instance.centro)

        fase_id = self.context['request'].data.get('fase_id')
        if fase_id:
            T_fase_ficha.objects.filter(
                ficha=instance, vige=1).update(fase_id=fase_id)

        instance.save()
        return instance


class RapSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_raps
        fields = ['id', 'nom']


class RapWriteSerializer(RapSerializer):
    compe = serializers.PrimaryKeyRelatedField(
        queryset=T_compe.objects.all()
    )
    fase = serializers.PrimaryKeyRelatedField(
        queryset=T_fase.objects.all(), many=True
    )

    class Meta(CompetenciaSerializer.Meta):
        fields = CompetenciaSerializer.Meta.fields + ['cod', 'compe', 'fase']

    def validate_nom(self, value):
        qs = T_raps.objects.filter(nom=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError(
                "Ya existe un RAP con ese nombre")
        return value

    def create(self, validated_data):
        fases = validated_data.pop('fase', [])
        validated_data['comple'] = "No"
        rap = T_raps.objects.create(**validated_data)
        rap.fase.set(fases)
        logger.warning(f"[CREATE RAP] Fases asociadas: {fases}")
        return rap

    def update(self, instance, validated_data):
        fases_ids = validated_data.pop('fase', [])

        for attr, value in validated_data.items():
          setattr(instance, attr, value)
        instance.save()

        if fases_ids is not None:
            instance.fase.set(fases_ids)
        return instance


class RapDetalleSerializer(RapSerializer):
    compe = serializers.PrimaryKeyRelatedField(queryset=T_compe.objects.all())
    programas = serializers.SerializerMethodField()
    fase = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )

    class Meta(RapSerializer.Meta):
        model = T_raps
        fields = RapSerializer.Meta.fields + \
            ['cod', 'compe', 'programas', 'fase']

    def get_programas(self, obj):
        return list(obj.compe.progra.values_list('id', flat=True))


class RapTablaSerializer(RapSerializer):
    compe = serializers.CharField(source="compe.nom", read_only=True)
    programas = serializers.SerializerMethodField()
    fase = serializers.SerializerMethodField()

    class Meta(RapSerializer.Meta):
        model = T_raps
        fields = RapSerializer.Meta.fields + ['cod', 'compe', 'programas', 'fase']

    def get_programas(self, obj):
        return [p.nom for p in obj.compe.progra.all()]
      
    def get_fase(self, obj):
      return [f.nom for f in obj.fase.all()]


class ProgramaSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_raps
        fields = ['id', 'nom']


class FaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_fase
        fields = ['id', 'nom']
