from api.serializers.dashboard import NovedadFiltrarSerializer, NovedadCrearSerializer, NovedadAccionSerializer, NovedadDetalleSerializer, NovedadDocumentoSerializer
from commons.models import (
    T_ficha, T_docu, T_apre,
    T_perfil, T_DocumentFolder,
    T_DocumentFolderAprendiz,
    T_jui_eva_actu, T_nove,
    T_acci_nove, T_nove_docu,
    T_acci_nove_docu)
from commons.utils.documentos import guardar_documento
from commons.utils.email import enviar_correo
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group,  User
from django.core.exceptions import ValidationError
from django.db import transaction, models
from django.db.models import Exists, OuterRef, Count, Q, DateField, Max, IntegerField
from django.db.models.functions import Cast
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, ModelViewSet


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
    queryset = T_nove.objects.all()
    serializer_class = NovedadFiltrarSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='filtrar')
    def filtrar(self, request):
        search = request.GET.get("search[value]", "").strip()
        order_col_index = request.GET.get("order[0][column]")
        order_dir = request.GET.get("order[0][dir]")

        user = request.user

        if not request.user.is_superuser:
            novedades = T_nove.objects.filter(Q(respo=user.id) | Q(soli=user.id))
        else:
            novedades = T_nove.objects.all()

        if search:
            novedades = novedades.filter(
                Q(num__icontains=search) |
                Q(descri__icontains=search) |
                Q(tipo__icontains=search) |
                Q(esta__icontains=search) |
                Q(fecha_venci__icontains=search)
            )

        paginated = self.paginate_queryset(novedades)

        data = NovedadFiltrarSerializer(paginated, many=True).data
        return self.get_paginated_response(data)

    @action(detail=False, methods=['post'], url_path='crear')
    @transaction.atomic
    def crear(self, request):
        serializer = NovedadCrearSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        default_respo = User.objects.filter(username="harcas1").first()
        default_group = default_respo.groups.first()

        def sumar_dias_habiles(fecha_inicio, dias):
            fecha = fecha_inicio
            dias_sumados = 0
            while dias_sumados < dias:
                fecha += timedelta(days=1)
                if fecha.weekday() < 5:
                    dias_sumados += 1
            return fecha

        fecha_actual = timezone.now()
        fecha_venci = sumar_dias_habiles(fecha_actual, 3)

        ultimo_num = (
            T_nove.objects.annotate(num_int=Cast("num", IntegerField()))
            .aggregate(max_num=Max("num_int"))
            .get("max_num")
        )

        nuevo_num = (ultimo_num or 0) + 1
        num_formateado = f"{nuevo_num:09d}"

        novedad = serializer.save(
            soli=user,
            respo=default_respo,
            respo_group=default_group,
            fecha_venci=fecha_venci,
            num=num_formateado,
        )

        T_acci_nove.objects.create(
            nove=novedad,
            crea_por=user,
            descri="Creación del caso",
        )

        documentos = request.FILES.getlist("documentos") or []
        for doc in documentos:
            new_doc = guardar_documento(
                archivo=doc,
                ruta=f"documentos/novedades/{novedad.id}/{doc.name}",
                max_size_mb=25
            )
            T_nove_docu.objects.create(nove=novedad, docu=new_doc)
        
        try:
            enviar_correo(
              destinatarios=[user.perfil.mail],
              asunto=f"Caso #{num_formateado} creado exitosamente",
              mensaje=f"Su caso #{num_formateado} ha sido creado correctamente y sera atendido en un plazo máximo de 3 días hábiles."
            )
            
            enviar_correo(
              destinatarios=[default_respo.perfil.mail],
              asunto=f"Nuevo caso asignado: #{num_formateado}",
              mensaje=f"Se le asigno un nuevo caso. por favor atender o hacer la resignación al respectivo grupo de ser necesario"
            )
        except Exception as e:
            print(f"Error enviando correo: {e}")
        
        return Response({"message": "Novedad creada exitosamente"}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='kpis')
    def kpis(self, request):
        user = request.user
        if user.is_superuser:
            novedades = T_nove.objects.all()
        else:
            novedades = T_nove.objects.filter(Q(respo=user.id) | Q(soli=user.id))

        kpis = {
            "total_novedades": novedades.count(),
            "nove_pendi": novedades.filter(esta__in=["nuevo", "pendiente", "planificacion", "reabierto"]).count(),
            "nove_gesti": novedades.filter(esta="en_curso").count(),
            "nove_cerra": novedades.filter(esta__in=["cerrado", "terminado"]).count(),
        }
        return Response(kpis, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='detalle')
    def detalle(self, request, pk=None):
        try:
            novedad = T_nove.objects.get(pk=pk)
        except T_nove.DoesNotExist:
            return Response({"error": "Novedad no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        serializer = NovedadDetalleSerializer(novedad)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='documentos')
    def documentos(self, request, pk=None):
        documentos = T_nove_docu.objects.filter(nove_id=pk)
        serializer = NovedadDocumentoSerializer(documentos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='acciones')
    def acciones(self, request, pk=None):
        acciones = T_acci_nove.objects.filter(nove_id=pk).order_by('-fecha')
        serializer = NovedadAccionSerializer(acciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='acciones/create')
    @transaction.atomic
    def crear_accion(self, request, pk=None):
        try:
            novedad = T_nove.objects.get(pk=pk)
        except T_nove.DoesNotExist:
            return Response({"error": "Novedad no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        descripcion = request.data.get("descri", "")
        if not descripcion.strip():
            return Response({"error": "La descripción es obligatoria"}, status=status.HTTP_400_BAD_REQUEST)

        accion = T_acci_nove.objects.create(
            nove=novedad,
            crea_por=request.user,
            descri=descripcion.strip(),
        )

        documentos = request.FILES.getlist("documentos") or []
        for doc in documentos:
            new_doc = guardar_documento(
                archivo=doc,
                ruta=f"documentos/novedades/{novedad.id}/acciones/{doc.name}",
                max_size_mb=25,
            )
            T_acci_nove_docu.objects.create(acci_nove=accion, docu=new_doc)

        try:
            enviar_correo(
              destinatarios=[novedad.soli.perfil.mail],
              asunto=f"Caso #{novedad.num} acción registrada",
              mensaje=f"Se ha registrado una nueva accion en el caso #{novedad.num}: {descripcion.strip()}."
            )
            
            enviar_correo(
              destinatarios=[novedad.respo.perfil.mail],
              asunto=f"Caso #{novedad.num} acción registrada",
              mensaje=f"Se ha registrado una nueva accion en el caso #{novedad.num}: {descripcion.strip()}."
            )
        except Exception as e:
            print(f"Error enviando correo: {e}")

        return Response({"message": "Acción creada exitosamente"}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='estados')
    def estados(self, request, pk=None):
        try:
            novedad = T_nove.objects.get(pk=pk)
        except T_nove.DoesNotExist:
            return Response({"error": "Novedad no encontrada"}, status=status.HTTP_400_BAD_REQUEST)

        estado = novedad.esta

        def get_estados_permitidos(estado_actual: str) -> list[str]:
            """
            Devuelve los estados a los que se puede cambiar desde el estado_actual.
            """
            transiciones = {
                "nuevo": ["en_curso", "pendiente", "rechazado"],
                "en_curso": ["planificacion", "pendiente", "rechazado", "terminado"],
                "pendiente": ["en_curso", "rechazado"],
                "planificacion": ["terminado", "pendiente", "rechazado"],
                "terminado": ["cerrado", "reabierto"],
                "rechazado": ["reabierto"],
                "cerrado": ["reabierto"],
                "reabierto": ["en_curso", "planificacion"],
            }

            return transiciones.get(estado_actual, [])

        estados_nove = get_estados_permitidos(estado)
        return Response(estados_nove, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path="estados/cambiar")
    def cambiar_estado(self, request, pk=None):
        try:
            novedad = T_nove.objects.get(pk=pk)
        except T_nove.DoesNotExist:
            return Response({"error": "Novedad no encontrada"}, status=status.HTTP_400_BAD_REQUEST)

        estado = request.data.get("estado", "")
        motivo_estado = request.data.get("motivo", "")
        if not estado.strip() or not motivo_estado.strip():
            return Response({"error": "Datos faltantes"}, status=status.HTTP_400_BAD_REQUEST)

        novedad.esta = estado
        novedad.motivo_solucion = motivo_estado
        novedad.save()

        try:
            enviar_correo(
              destinatarios=[novedad.soli.perfil.mail],
              asunto=f"Caso #{novedad.num} cambio de estado",
              mensaje=f"Se ha actualizado el estado del caso #{novedad.num} a {novedad.esta}."
            )
            
            enviar_correo(
              destinatarios=[novedad.respo.perfil.mail],
              asunto=f"Caso #{novedad.num} cambio de estado",
              mensaje=f"Se ha actualizado el estado del caso #{novedad.num} a {novedad.esta}."
            )
        except Exception as e:
            print(f"Error enviando correo: {e}")

        
        return Response({"message": "Estado actualizado"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path="asignado")
    def asignado(self, request, pk=None):
        grupos = Group.objects.all()
        data = {
            "grupos": [],
            "personas": {}
        }
        for g in grupos:
            data["grupos"].append({
                "id": g.id,
                "nombre": g.name
            })

            usuarios = g.user_set.select_related("perfil").all()
            
            personas = []
            
            for u in usuarios:
                perfil = getattr(u, "perfil", None)
                if perfil:
                    nombre = f"{perfil.nom} {perfil.apelli}".strip()
                else:
                    nombre = u.username
                
                personas.append({
                    "id": u.id,
                    "nombre": nombre
                })
                
            data["personas"][str(g.id)] = personas
        
        return Response(data, status=status.HTTP_200_OK)
      
    @action(detail=True, methods=['post'], url_path="asignado/guardar")
    def guardar_asignado(self, request, pk=None):
        try:
            novedad = T_nove.objects.get(pk=pk)
        except T_nove.DoesNotExist:
            return Response({"error": "Novedad no encontrada"}, status=status.HTTP_400_BAD_REQUEST)

        grupo = request.data.get("grupo")
        persona = request.data.get("persona")

        if not grupo.strip() or not persona.strip():
            return Response({"error": "Datos faltantes"}, status=status.HTTP_400_BAD_REQUEST)

        if novedad.respo_id == int(persona):
            return Response({"error": "El caso ya esta asignado a esta persona"}, status=status.HTTP_400_BAD_REQUEST)

        novedad.respo_group_id = grupo
        novedad.respo_id = persona
        novedad.save()
        
        try:
            enviar_correo(
              destinatarios=[novedad.soli.perfil.mail],
              asunto=f"Caso #{novedad.num} asignado",
              mensaje=f"Su caso #{novedad.num} ha sido asignado al grupo {novedad.respo_group.name}."
            )
            
            enviar_correo(
              destinatarios=[novedad.respo.perfil.mail],
              asunto=f"Nuevo caso asignado: #{novedad.num}",
              mensaje=f"Se le asigno un nuevo caso. por favor atender o hacer la resignación al respectivo grupo de ser necesario"
            )
        except Exception as e:
            print(f"Error enviando correo: {e}")

        return Response({"message": "Responsable actualizado"}, status=status.HTTP_200_OK)