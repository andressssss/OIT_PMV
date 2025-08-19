from rest_framework import serializers
from commons.models import T_perfil, T_departa, T_munici, T_insti_edu, T_centro_forma, T_apre, T_ficha, T_repre_legal


class PerfilSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source='user.username', read_only=True)
    last_login = serializers.DateTimeField(
        source='user.last_login', read_only=True)

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


class DepartamentoSerializer(serializers.ModelSerializer):
    nom = serializers.CharField(source='nom_departa')

    class Meta:
        model = T_departa
        fields = ['id', 'nom']


class MunicipioSerializer(serializers.ModelSerializer):
    nom = serializers.CharField(source='nom_munici')
    depa_id = serializers.IntegerField(source='nom_departa_id')

    class Meta:
        model = T_munici
        fields = ['id', 'nom', 'depa_id']


class InstitucionSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_insti_edu
        fields = ['id', 'nom', 'muni_id']


class CentroFormacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_centro_forma
        fields = ['id', 'nom']


class RepresentanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_repre_legal
        fields = ['nom', 'dni', 'tele', 'dire', 'mail', 'paren']


class AprendizSerializer(serializers.ModelSerializer):
    perfil = PerfilSerializer()
    repre_legal = RepresentanteSerializer(required=False, allow_null=True)

    class Meta:
        model = T_apre
        fields = [
            'id',
            'perfil',
            'repre_legal',
            'ficha',
            'esta'
        ]

    def validate(self, data):
        perfil_data = data.get('perfil', {})
        mail = perfil_data.get('mail')
        dni = perfil_data.get('dni')

        instance = getattr(self, 'instance', None)

        if mail and T_perfil.objects.exclude(id=instance.perfil.id).filter(mail=mail).exists():
            raise serializers.ValidationError({'email': 'Ya existe un perfil con este correo electrónico.'})

        if dni and T_perfil.objects.exclude(id=instance.perfil.id).filter(dni=dni).exists():
            raise serializers.ValidationError({'dni': 'Ya existe un perfil con este número de documento.'})

        return data

    def update(self, instance, validated_data):
        perfil_data = validated_data.pop('perfil', {})
        for attr, value in perfil_data.items():
            setattr(instance.perfil, attr, value)
        instance.perfil.save()

        repre_data = validated_data.pop('repre_legal', serializers.empty)

        if repre_data is None:
            if instance.repre_legal:
                instance.repre_legal.delete()
                instance.repre_legal = None

        elif repre_data is not serializers.empty:
            campos_obligatorios = ['nom', 'dni', 'paren']
            tiene_datos = any(repre_data.get(campo) for campo in campos_obligatorios)

            if tiene_datos:
                if instance.repre_legal:
                    for attr, value in repre_data.items():
                        setattr(instance.repre_legal, attr, value)
                    instance.repre_legal.save()
                else:
                    nuevo_repre = T_repre_legal.objects.create(**repre_data)
                    instance.repre_legal = nuevo_repre
            else:
                # Todos los campos vacíos → eliminar si existe
                if instance.repre_legal:
                    instance.repre_legal.delete()
                    instance.repre_legal = None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
      