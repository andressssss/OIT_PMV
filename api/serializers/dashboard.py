from commons.models import T_nove, T_nove_docu, T_acci_nove, T_acci_nove_docu, T_perfil
from rest_framework import serializers

class NovedadCrearSerializer(serializers.ModelSerializer):
    class Meta:
        model = T_nove
        fields = ["descri", "tipo"]

class NovedadFiltrarSerializer(serializers.ModelSerializer):
    fecha = serializers.DateTimeField(source='fecha_venci', format="%Y-%m-%d %H:%M:%S")
    responsable = serializers.SerializerMethodField()

    class Meta:
        model = T_nove
        fields = ["id", "num", "tipo", "descri", "esta", "fecha", "responsable"]
    
    def get_responsable(self, obj):
        perfil = T_perfil.objects.get(user_id=obj.respo)
        return f"{perfil.nom} {perfil.apelli}"
        
class NovedadDetalleSerializer(serializers.ModelSerializer):
    respo_nom = serializers.SerializerMethodField()
    soli_nom = serializers.SerializerMethodField()
    fecha_regi = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    fecha_venci = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    grupo = serializers.CharField(source="respo_group.name")
    class Meta:
        model = T_nove
        fields = ['id', 'num', 'tipo', 'esta', 'descri', 'fecha_regi', 'fecha_venci', "tipo", "soli_nom", "respo_nom", "descri", "motivo_solucion", "grupo"]
        
    def get_respo_nom(self, obj):
        return f"{obj.respo.perfil.nom} {obj.respo.perfil.apelli}"
      
    def get_soli_nom(self, obj):
        return f"{obj.soli.perfil.nom} {obj.soli.perfil.apelli}"

class NovedadDocumentoSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='docu.nom')
    tipo = serializers.CharField(source='docu.tipo')
    url = serializers.SerializerMethodField()
    class Meta:
        model = T_nove_docu
        fields = ['id', 'docu', 'nombre', 'tipo', 'url']
        
    def get_url(self, obj):
        return obj.docu.archi.url

class NovedadAccionSerializer(serializers.ModelSerializer):
    documentos = serializers.SerializerMethodField()
    crea_por_nombre = serializers.SerializerMethodField()
    fecha = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = T_acci_nove
        fields = ['id', 'descri', 'fecha', 'crea_por_nombre', 'documentos']

    def get_crea_por_nombre(self, obj):
        perfil = getattr(obj.crea_por, 'perfil', None)
        if perfil:
            return f"{perfil.nom} {perfil.apelli}"
        return "Sin usuario"

    def get_documentos(self, obj):
        # Trae todos los documentos vinculados a la acción
        docs = T_acci_nove_docu.objects.filter(acci_nove=obj).select_related('docu')
        return [
            {
                "nombre": doc.docu.nom if doc.docu else "Documento sin nombre",
                "url": doc.docu.archi.url if doc.docu and doc.docu.archi else None,
            }
            for doc in docs
        ]
