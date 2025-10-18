from django.db.models import Exists, OuterRef
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Count
from django.contrib.auth import get_user_model
from commons.models import T_ficha, T_docu, T_apre, T_perfil, T_DocumentFolder, T_DocumentFolderAprendiz, T_jui_eva_actu, T_nove
from django.db.models import Q, DateField
from api.serializers.dashboard import NovedadFiltrarSerializer

User = get_user_model()


class DashboardKpisView(APIView):
    def get(self, request):
        documentos_ficha = T_DocumentFolder.objects.filter(
            tipo="documento").count()
        documentos_aprendices = T_DocumentFolderAprendiz.objects.filter(
            tipo="documento").count()

        # --- Carpetas vacías en fichas ---
        carpetas_ficha = T_DocumentFolder.objects.filter(tipo="carpeta").annotate(
            tiene_subcarpeta=Exists(
                T_DocumentFolder.objects.filter(
                    parent=OuterRef('pk'),
                    tipo="carpeta"
                )
            ),
            tiene_documento=Exists(
                T_DocumentFolder.objects.filter(
                    parent=OuterRef('pk'),
                    tipo="documento"
                )
            )
        ).filter(
            tiene_subcarpeta=False,
            tiene_documento=False
        )
        total_carpetas_ficha = carpetas_ficha.count()

        # --- Carpetas vacías en aprendices ---
        carpetas_apre = T_DocumentFolderAprendiz.objects.filter(tipo="carpeta").annotate(
            tiene_subcarpeta=Exists(
                T_DocumentFolderAprendiz.objects.filter(
                    parent=OuterRef('pk'),
                    tipo="carpeta"
                )
            ),
            tiene_documento=Exists(
                T_DocumentFolderAprendiz.objects.filter(
                    parent=OuterRef('pk'),
                    tipo="documento"
                )
            )
        ).filter(
            tiene_subcarpeta=False,
            tiene_documento=False
        )
        total_carpetas_apre = carpetas_apre.count()

        # Total de fichas
        total_fichas = T_ficha.objects.count()

        # Fichas que tienen juicios (distintas en la tabla de evaluaciones)
        fichas_con_juicios = T_jui_eva_actu.objects.values(
            "ficha").distinct().count()

        # Fichas que no tienen juicios
        fichas_sin_juicios = total_fichas - fichas_con_juicios

        data = {
            "total_fichas": total_fichas,
            "fichas_con_juicios": fichas_con_juicios,
            "fichas_sin_juicios": fichas_sin_juicios,
            "usuarios_activos": User.objects.filter(is_active=True).count(),
            "usuarios_inactivos": User.objects.filter(is_active=False).count(),
            "usuarios_total": User.objects.count(),
            "documentos_total": documentos_ficha + documentos_aprendices,
            "documentos_fichas": documentos_ficha,
            "documentos_aprendices": documentos_aprendices,
            "carpetas_vacias_total": total_carpetas_ficha + total_carpetas_apre,
            "carpetas_vacias_fichas": total_carpetas_ficha,
            "carpetas_vacias_aprendices": total_carpetas_apre,
        }

        return Response(data, status=status.HTTP_200_OK)


class DashboardFichasView(APIView):
    def get(self, request):
        fichas = (
            T_ficha.objects.values("progra__nom")
            .annotate(total=Count("id"))
        )

        # Diccionario de apodos
        aliases = {
            "PROGRAMACION PARA ANALITICA DE DATOS": "P. ANALITICA DE DATOS",
            "PROGRAMACION DE APLICACIONES Y SERVICIOS PARA LA NUBE": "P. APPS EN LA NUBE",
            "CONTROL DE LA SEGURIDAD DIGITAL": "SEGURIDAD DIGITAL",
            "MANTENIMIENTO DE EQUIPOS DE COMPUTO": "MANT. EQUIPOS",
            "INTEGRACION DE CONTENIDOS DIGITALES": "CONTENIDOS DIGITALES",
            "IMPLEMENTACION Y MANTENIMIENTO DE SISTEMAS DE INTERNET DE LAS COSAS": "IoT",
            "PROGRAMACION DE APLICACIONES PARA DISPOSITIVOS MOVILES": "P. APPS MOVILES",
            "SISTEMAS TELEINFORMATICOS": "TELEINFORMATICA",
            "PROGRAMACION DE SOFTWARE": "P. SOFTWARE",
        }

        resultado = [
            {
                "alias": aliases.get(f["progra__nom"], f["progra__nom"]),
                "nombre": f["progra__nom"],
                "total": f["total"]
            }
            for f in fichas
        ]

        return Response(resultado, status=status.HTTP_200_OK)


class UsuariosPorRolView(APIView):
    def get(self, request):
        data = (
            T_perfil.objects.values("rol")
            .annotate(total=Count("id"))
            .order_by("rol")
        )

        resultado = [
            {
                "alias": i["rol"].capitalize(),
                "nombre": i["rol"],
                "total": i["total"]
            }
            for i in data
        ]

        return Response(resultado, status=status.HTTP_200_OK)


class DashboardRapsView(APIView):
    def get(self, request):
        evaluados = T_jui_eva_actu.objects.filter(eva="APROBADO").count()
        por_evaluar = T_jui_eva_actu.objects.filter(eva="POR EVALUAR").count()

        resultado = [
            {"alias": "Evaluados", "nombre": "evaluados", "total": evaluados},
            {"alias": "Por Evaluar", "nombre": "por_evaluar", "total": por_evaluar},
        ]

        return Response(resultado, status=status.HTTP_200_OK)


class NovedadesViewSet(ModelViewSet):
    queryset = T_apre.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='filtrar')
    def filtrar(self, request):
        search = request.GET.get("search[value]", "").strip()
        order_col_index = request.GET.get("order[0][column]")
        order_dir = request.GET.get("order[0][dir]")

        novedades = T_nove.objects.all()
        
        if search:
            novedades = novedades.filter(
                Q(num__icontains=search) |
                Q(descri__icontains=search) |
                Q(tipo__icontains=search) |
                Q(esta__icontains=search) |
                Q(fecha__icontains=search)
            )
            
        paginated = self.paginate_queryset(novedades)
        
        data = NovedadFiltrarSerializer(paginated, many=True).data
        return self.get_paginated_response(data)
