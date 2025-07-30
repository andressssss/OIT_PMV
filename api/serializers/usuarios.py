from rest_framework import serializers
from commons.models import T_perfil, T_departa, T_munici, T_insti_edu, T_centro_forma, T_apre, T_ficha

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
        model= T_centro_forma
        fields= ['id', 'nom']

class AprendizSerializer(serializers.ModelSerializer):
    nom = serializers.SerializerMethodField()
    apelli = serializers.SerializerMethodField()
    tele = serializers.SerializerMethodField()
    dire = serializers.SerializerMethodField()
    mail = serializers.SerializerMethodField()
    fecha_naci = serializers.SerializerMethodField()
    tipo_dni = serializers.SerializerMethodField()
    dni = serializers.SerializerMethodField()

    class Meta:
        model = T_apre
        fields = [
          'id',
          'nom',
          'apelli',
          'tele',
          'dire',
          'mail',
          'fecha_naci',
          'tipo_dni',
          'dni',
          'esta'
        ]
        
    def get_nom(self, obj):
      return obj.perfil.nom
    
    def get_apelli(self, obj):
      return obj.perfil.apelli
    
    def get_tele(self, obj):
      return obj.perfil.tele
    
    def get_dire(self, obj):
      return obj.perfil.dire
    
    def get_mail(self, obj):
      return obj.perfil.mail
    
    def get_fecha_naci(self, obj):
      return obj.perfil.fecha_naci
    
    def get_tipo_dni(self, obj):
      return obj.perfil.tipo_dni
    
    def get_dni(self, obj):
      return obj.perfil.dni
