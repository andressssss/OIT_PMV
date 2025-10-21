from commons.models import T_nove, T_nove_docu, T_acci_nove
from rest_framework import serializers

class NovedadCrearSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_nove
        fields = ["descri", "tipo"]

class NovedadFiltrarSerializer(serializers.ModelSerializer):
    fecha = serializers.DateTimeField(source='fecha_regi', format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = T_nove
        fields = ["id", "num", "tipo", "descri", "esta", "fecha"]
        
class NovedadDetalleSerializer(serializers.ModelSerializer):
    respo_nom = serializers.SerializerMethodField()
    soli_nom = serializers.SerializerMethodField()
    fecha_regi = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    fecha_venci = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    
    class Meta:
        model = T_nove
        fields = ['id', 'num', 'tipo', 'esta', 'descri', 'fecha_regi', 'fecha_venci', "tipo", "soli_nom", "respo_nom", "descri"]
        
    def get_respo_nom(self, obj):
        return f"{obj.respo.perfil.nom} {obj.respo.perfil.apelli}"
      
    def get_soli_nom(self, obj):
        return f"{obj.soli.perfil.nom} {obj.soli.perfil.apelli}"

class NovedadDocumentoSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='docu.nom')
    tipo = serializers.CharField(source='docu.tipo')
    url = serializers.CharField(source='docu.archi')
    class Meta:
        model = T_nove_docu
        fields = ['id', 'docu', 'nombre', 'tipo', 'url']

class NovedadAccionSerializer(serializers.ModelSerializer):
    documentos = NovedadDocumentoSerializer(many=True, read_only=True, source='t_nove_docu_set')
    crea_por_nombre = serializers.SerializerMethodField()
    fecha = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    
    class Meta:
        model = T_acci_nove
        fields = ['id', 'descri', 'fecha', 'crea_por_nombre', 'documentos']

    def get_crea_por_nombre(self, obj):
        return f"{obj.crea_por.perfil.nom} {obj.crea_por.perfil.apelli}"