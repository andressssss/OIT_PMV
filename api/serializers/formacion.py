from rest_framework import serializers
from commons.models import T_raps, T_compe, T_ficha, T_fase, T_fase_ficha, T_insti_edu, T_centro_forma, T_jui_eva_actu, T_jui_eva_diff
import logging

logger = logging.getLogger(__name__)


# Serializers reutilizables
class CompetenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_compe
        fields = ['id', 'nom']


class CompetenciaWriteSerializer(CompetenciaSerializer):

    class Meta(CompetenciaSerializer.Meta):
        fields = CompetenciaSerializer.Meta.fields + ['cod']

    def validate_nom(self, value):
        qs = T_compe.objects.filter(nom__iexact=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Ya existe una competencia con este nombre.")
        return value

    def create(self, validated_data):
        competencia = T_compe.objects.create(**validated_data)
        return competencia

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance


class CompetenciaDetalleSerializer(CompetenciaSerializer):
    class Meta(CompetenciaSerializer.Meta):
        fields = CompetenciaSerializer.Meta.fields + ['cod']


class CompetenciaTablaSerializer(CompetenciaSerializer):
    class Meta(CompetenciaSerializer.Meta):
        fields = CompetenciaSerializer.Meta.fields + ['cod']


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

    class Meta(RapSerializer.Meta):
        fields = RapSerializer.Meta.fields + ['cod', 'compe', 'progra', 'fase']

    def validate_cod(self, value):
        qs = T_raps.objects.filter(cod=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError(
                "Ya existe un RAP con ese código")
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
    fase = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )

    class Meta(RapSerializer.Meta):
        model = T_raps
        fields = RapSerializer.Meta.fields + \
            ['cod', 'compe', 'progra', 'fase']


class RapTablaSerializer(RapSerializer):
    compe = serializers.CharField(source="compe.nom", read_only=True)
    progra = serializers.CharField(source="progra.nom", read_only=True)
    fase = serializers.SerializerMethodField()

    class Meta(RapSerializer.Meta):
        model = T_raps
        fields = RapSerializer.Meta.fields + ['cod', 'compe', 'progra', 'fase']

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


class JuicioSerializer(serializers.ModelSerializer):
    apre_nom = serializers.SerializerMethodField()
    ficha_num = serializers.CharField(source="ficha.num", read_only="true")
    instru_nom = serializers.SerializerMethodField()
    rap_nom = serializers.CharField(source="rap.nom", read_only="true")
    fecha = serializers.SerializerMethodField()

    class Meta:
        model = T_jui_eva_actu
        fields = ['fecha_repor', 'eva', 'fecha', 'apre_nom',
                  'ficha_num', 'instru_nom', 'rap_nom']

    def get_apre_nom(self, obj):
        return f"{obj.apre.perfil.nom} {obj.apre.perfil.apelli}"

    def get_instru_nom(self, obj):
        return "Sin registro" if obj.instru is None else f"{obj.instru.perfil.nom} {obj.instru.perfil.apelli}"

    def get_fecha(self, obj):
        return "Sin registro" if obj.fecha_eva is None else obj.fecha_eva

class JuicioHistoSerializer(serializers.ModelSerializer):
    apre_nom = serializers.SerializerMethodField()
    instru_nom = serializers.SerializerMethodField()
    jui_desc = serializers.SerializerMethodField()
    tipo_cambi = serializers.SerializerMethodField()
    
    class Meta:
        model = T_jui_eva_diff
        fields = ['tipo_cambi', 'descri', 'fecha_diff', 'apre_nom', 'instru_nom', 'jui_desc']
        
    def get_apre_nom(self, obj):
        return f"{obj.apre.perfil.nom} {obj.apre.perfil.apelli}"
      
    def get_instru_nom(self, obj):
        return "Sin registro" if obj.instru is None else f"{obj.instru.perfil.nom} {obj.instru.perfil.apelli}"
    
    def get_jui_desc(self, obj):
        return "N/A" if obj.jui is None else f"Juicio:{obj.jui.rap.cod}. Aprendiz:{obj.jui.apre.perfil.dni}"
      
    def get_tipo_cambi(self, obj):
        return obj.tipo_cambi.capitalize()
