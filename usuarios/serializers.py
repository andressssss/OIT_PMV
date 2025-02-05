from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from commons.models import T_insti_edu

class T_insti_edu_Serializer(ModelSerializer):
    municipio_nombre = serializers.CharField(source='muni.nom_munici', read_only=True)
    departamento_nombre = serializers.CharField(source='muni.nom_departa.nom_departa', read_only=True)

    class Meta:
        model = T_insti_edu
        fields = ['id', 'nom', 'dire', 'municipio_nombre', 'departamento_nombre', 'secto', 'esta','dane', 'gene', 'zona']
