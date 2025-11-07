from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework.pagination import PageNumberPagination
from django.core.files.storage import default_storage
from django.contrib.contenttypes.models import ContentType
from datetime import datetime
from io import TextIOWrapper
from django.db import transaction
from django.forms import ValidationError
from django.utils import timezone
from django.db.models import Q
import csv
from django.shortcuts import get_object_or_404
from api.serializers.formacion import FaseSerializer, JuicioHistoSerializer, JuicioSerializer,  RapSerializer, RapWriteSerializer, RapTablaSerializer, RapDetalleSerializer, CompetenciaTablaSerializer, CompetenciaWriteSerializer, CompetenciaSerializer, CompetenciaDetalleSerializer, FichaSerializer, FichaEditarSerializer, ProgramaSerializer, JuicioHistoSerializer, FichaFiltrarSerializer, PortaArchiSerializer
from commons.models import T_jui_eva_actu, T_fase, T_raps, AuditLog, T_compe, T_ficha, T_prematri_docu, T_DocumentFolder, T_docu, T_apre, T_centro_forma, T_progra, T_insti_edu, T_perfil, T_instru, T_gestor_grupo, T_grupo, T_fase_ficha, T_gestor_depa, T_gestor, T_DocumentFolderAprendiz, T_jui_eva_diff, T_porta_archi
from django.contrib.auth.models import User
from django.utils.timezone import localtime
from matricula.scripts.cargar_tree import crear_datos_prueba
from matricula.scripts.cargar_tree_apre import crear_datos_prueba_aprendiz
from commons.permisos import DenegarConsulta
from commons.mixins import PermisosMixin

import logging

logger = logging.getLogger(__name__)


class DataTablesPagination(PageNumberPagination):
    page_size_query_param = 'length'
    page_query_param = 'start'

    def paginate_queryset(self, queryset, request, view=None):
        try:
            self.offset = int(request.query_params.get('start', 0))
            self.limit = int(request.query_params.get(
                'length', self.page_size))
            self.count = queryset.count()
            self.request = request
            return list(queryset[self.offset:self.offset + self.limit])
        except (ValueError, TypeError):
            return None

    def get_paginated_response(self, data):
        return Response({
            'recordsTotal': self.count,
            'recordsFiltered': self.count,
            'data': data
        })


class RapsViewSet(ModelViewSet):
    queryset = T_raps.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RapDetalleSerializer
        elif self.action == 'tabla':
            return RapTablaSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RapWriteSerializer
        return RapSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        rap_nom = instance.nom

        instance.fase.clear()
        instance.delete()

        return Response({
            'status': 'success',
            'message': f'RAP {rap_nom} eliminado correctamente'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='tabla')
    def tabla(self, request):
        programas = request.GET.getlist('programas', [])
        fases = request.GET.getlist('fases', [])
        competencias = request.GET.getlist('competencias', [])
        qs = self.get_queryset()

        if programas:
            qs = qs.filter(progra__nom__in=programas)

        if fases:
            qs = qs.filter(fase__nom__in=fases)

        if competencias:
            qs = qs.filter(compe__nom__in=competencias)

        data = self.get_serializer(qs, many=True).data

        can_edit = PermisosMixin().get_permission_actions_for(
            request, "raps").get("editar", False)
        for d in data:
            d["can_edit"] = can_edit

        return Response(data)


class CompetenciasViewSet(ModelViewSet):
    queryset = T_compe.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        programa_id = self.request.query_params.get('programa')
        if programa_id:
            queryset = queryset.filter(progra__id=programa_id)
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CompetenciaDetalleSerializer
        elif self.action == 'tabla':
            return CompetenciaTablaSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CompetenciaWriteSerializer
        return CompetenciaSerializer

    def destroy(self, request, *args, **kwargs):
        competencia = self.get_object()

        if T_raps.objects.filter(compe=competencia).exists():
            return Response(
                {"detail": "No se puede eliminar. Hay RAPS asociados a esta competencia."},
                status=status.HTTP_400_BAD_REQUEST
            )

        super().destroy(request, *args, **kwargs)
        return Response(
            {"message": "Competencia eliminada correctamente"},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='tabla')
    def tabla(self, request):
        programas = request.GET.getlist('programas', [])
        qs = self.get_queryset()

        if programas:
            qs = qs.filter(progra__nom__in=programas)

        can_edit = PermisosMixin().get_permission_actions_for(
            request, "competencias").get("editar", False)

        data = self.get_serializer(qs, many=True).data

        for item in data:
            item["can_edit"] = can_edit

        return Response(data)


class FichasViewSet(ModelViewSet):
    queryset = T_ficha.objects.all()
    serializer_class = FichaSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]
    pagination_class = DataTablesPagination

    def get_serializer_class(self):
        if self.action in ['list', 'fichas_por_programa']:
            return FichaSerializer
        return FichaEditarSerializer

    @action(detail=False, methods=['get'], url_path='por_programa/(?P<programa_id>[^/.]+)')
    def fichas_por_programa(self, request, programa_id=None):
        fichas = self.get_queryset().filter(progra=programa_id)
        serializer = self.get_serializer(fichas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='crear_carpeta')
    def crear_carpeta(self, request, pk=None):
        nombre = request.data.get("nombre", "").strip()
        parent_id = request.data.get("parent_id", "")

        if not nombre:
            return Response({
                "message": "El nombre de la carpeta es obligatorio."
            }, status=status.HTTP_400_BAD_REQUEST)

        ficha = self.get_object()

        if T_DocumentFolder.objects.filter(name=nombre, ficha=ficha, parent_id=parent_id or None, tipo='carpeta').exists():
            return Response({
                "Message": "Ya existe una carpeta con ese nombre en esta ubicación."
            })

        nueva_carpeta = T_DocumentFolder.objects.create(
            name=nombre,
            parent_id=parent_id,
            ficha=ficha,
            tipo="carpetap"
        )

        return Response({
            "message": "Carpeta creada correctamente"
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='importar', parser_classes=[MultiPartParser])
    def importar_fichas_csv(self, request):
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({"message": "No se envió ningún archivo"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lector = csv.DictReader(TextIOWrapper(
                archivo.file, encoding='utf-8-sig'), delimiter=';')
        except Exception as e:
            return Response({"message": "Archivo invalido", "errores": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)

        errores = []
        resumen = {'insertados': 0}

        try:
            with transaction.atomic():
                for i, fila in enumerate(lector, start=2):
                    required_fields = ['num_ficha', 'fase', 'cod_centro_forma',
                                       'dane_insti', 'nombre_progra', 'cedula_instru']
                    missing = [field for field in required_fields if not fila.get(
                        field, '').strip()]
                    if missing:
                        raise ValidationError(
                            f"Fila {i}: Campos faltantes: {', '.join(missing)}")

                    num_ficha = fila['num_ficha'].strip()
                    fase_actual = fila['fase'].strip()

                    # 🚨 Validaciones críticas — si fallan, se detiene TODO
                    try:
                        centro = T_centro_forma.objects.get(
                            cod=fila['cod_centro_forma'])
                    except T_centro_forma.DoesNotExist:
                        raise ValidationError(
                            f"Fila {i}: Centro de formación '{fila['cod_centro_forma']}' no encontrado")

                    try:
                        institucion = T_insti_edu.objects.get(
                            dane=fila['dane_insti'])
                    except T_insti_edu.DoesNotExist:
                        raise ValidationError(
                            f"Fila {i}: Institución con DANE '{fila['dane_insti']}' no encontrada")

                    try:
                        programa = T_progra.objects.get(
                            nom=fila['nombre_progra'])
                    except T_progra.DoesNotExist:
                        raise ValidationError(
                            f"Fila {i}: Programa '{fila['nombre_progra']}' no encontrado")

                    # Instructor opcional
                    cedula = fila['cedula_instru'].strip()
                    if cedula in ['0', '']:
                        instructor = None
                    else:
                        try:
                            perfil_instru = T_perfil.objects.get(dni=cedula)
                            instructor = T_instru.objects.get(
                                perfil=perfil_instru)
                        except (T_perfil.DoesNotExist, T_instru.DoesNotExist):
                            raise ValidationError(
                                f"Fila {i}: Instructor con cédula '{cedula}' no encontrado")

                    if T_ficha.objects.filter(num=num_ficha).exists():
                        raise ValidationError(
                            f"Fila {i}: La ficha {num_ficha} ya existe.")

                    # 👇 Toda esta parte permanece igual
                    grupo = T_grupo.objects.create(
                        esta='Masivo',
                        fecha_crea=timezone.now(),
                        autor=request.user,
                        centro=centro,
                        insti=institucion,
                        progra=programa
                    )

                    ficha = T_ficha.objects.create(
                        num=num_ficha,
                        grupo=grupo,
                        fecha_aper=timezone.now(),
                        insti=institucion,
                        centro=centro,
                        progra=programa,
                        esta="Activo",
                        instru=instructor,
                        num_apre_forma=0,
                        num_apre_pendi_regi=0,
                        num_apre_proce=0
                    )

                    departamento = institucion.muni.nom_departa if institucion and institucion.muni else None
                    gestor_depa = T_gestor_depa.objects.filter(
                        depa=departamento).select_related('gestor').first()
                    gestor = gestor_depa.gestor if gestor_depa else T_gestor.objects.get(
                        pk=1)

                    T_gestor_grupo.objects.create(
                        fecha_crea=timezone.now(),
                        autor=request.user,
                        gestor=gestor,
                        grupo=grupo
                    )

                    for f in range(1, int(fase_actual)):
                        T_fase_ficha.objects.create(
                            fase_id=f, ficha=ficha, fecha_ini=timezone.now(), instru=instructor, vige=0)
                    T_fase_ficha.objects.create(
                        fase_id=fase_actual, ficha=ficha, fecha_ini=timezone.now(), instru=instructor, vige=1)

                    crear_datos_prueba(ficha.id)
                    resumen['insertados'] += 1

                return Response({'message': 'Fichas importadas correctamente.', 'resumen': resumen}, status=201)

        except ValidationError as e:
            return Response({'message': 'Error de validación', 'errores': [str(e)]}, status=400)
        except Exception as e:
            return Response({'message': 'Error crítico', 'errores': [str(e)]}, status=500)

    @action(detail=False, methods=['post'], url_path='asignar_apre', parser_classes=[MultiPartParser])
    def asignar_aprendices_fichas(self, request):
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({"message": "No se envió ningún archivo"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lector = csv.DictReader(TextIOWrapper(
                archivo.file, encoding='utf-8-sig'), delimiter=';')
        except Exception as e:
            return Response({"message": "Archivo inválido", "errores": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)

        errores = []
        resumen = {'insertados': 0}
        documentos_matricula = [
            'Documento de Identidad del aprendiz',
            'Registro civil',
            'Certificado de Afiliación de salud',
            'Formato de Tratamiento de Datos del Menor de Edad',
            'Compromiso del Aprendiz',
        ]

        fichas_modificadas = set()

        try:
            with transaction.atomic():
                for i, fila in enumerate(lector, start=2):
                    try:
                        required_fields = [
                            'nom', 'apelli', 'email', 'tipo_dni', 'dni', 'tele', 'gene', 'num_ficha']
                        missing = [field for field in required_fields if not fila.get(
                            field, '').strip()]
                        if missing:
                            raise ValidationError(
                                f"Campos faltantes: {', '.join(missing)}")

                        dni = fila['dni'].strip()
                        email = fila['email'].strip()
                        ficha_num = fila['num_ficha'].strip()

                        # Validación de existencia de DNI o email
                        if T_perfil.objects.filter(dni=dni).exists():
                            raise ValidationError(
                                f"El DNI '{dni}' ya está registrado.")
                        if T_perfil.objects.filter(mail=email).exists():
                            raise ValidationError(
                                f"El correo '{email}' ya está registrado.")

                        try:
                            ficha = T_ficha.objects.get(num=ficha_num)
                        except T_ficha.DoesNotExist:
                            raise ValidationError(
                                f"La ficha {ficha_num} no existe!")

                        fichas_modificadas.add(ficha.id)
                        fecha_naci = fila['fecha_naci']
                        if fecha_naci:
                            fecha_naci = datetime.strptime(
                                fila['fecha_naci'].strip(), '%d/%m/%Y').date()
                        else:
                            fecha_naci = None
                        base_username = (
                            fila['nom'][:3] + fila['apelli'][:3]).lower()
                        username = base_username
                        contador = 1
                        while User.objects.filter(username=username).exists():
                            username = f"{base_username}{contador}"
                            contador += 1

                        new_user = User.objects.create_user(
                            username=username,
                            password=str(dni),
                            email=email
                        )

                        new_perfil = T_perfil.objects.create(
                            user=new_user,
                            nom=fila['nom'],
                            apelli=fila['apelli'],
                            tipo_dni=fila['tipo_dni'],
                            dni=dni,
                            tele=fila['tele'],
                            dire=fila['dire'],
                            gene=fila['gene'],
                            mail=email,
                            fecha_naci=fecha_naci,
                            rol="aprendiz"
                        )
                        new_perfil.full_clean()

                        new_aprendiz = T_apre.objects.create(
                            cod="z",
                            esta="activo",
                            perfil=new_perfil,
                            grupo=ficha.grupo,
                            ficha=ficha,
                            usu_crea=request.user,
                            esta_docu="Pendiente"
                        )
                        new_aprendiz.full_clean()

                        for documento in documentos_matricula:
                            T_prematri_docu.objects.create(
                                nom=documento,
                                apren=new_aprendiz,
                                esta="Pendiente",
                                vali="0"
                            )
                        crear_datos_prueba_aprendiz(new_aprendiz.id)
                        resumen["insertados"] += 1

                    except Exception as e:
                        errores.append(f"Fila {i}: {str(e)}")
                        raise ValidationError(f"Fila {i}: {str(e)}")

                # Actualiza las fichas afectadas
                for ficha_id in fichas_modificadas:
                    ficha = T_ficha.objects.get(id=ficha_id)
                    aprendices_totales = T_apre.objects.filter(
                        ficha=ficha).count()
                    ficha.num_apre_pendi_regi = aprendices_totales
                    ficha.num_apre_proce = aprendices_totales
                    ficha.save()

            if errores:
                return Response({'message': 'Errores al importar.', 'errores': errores}, status=400)

            return Response({'message': 'Aprendices importados correctamente.', 'resumen': resumen}, status=201)

        except Exception as e:
            return Response({'message': 'Error crítico', 'errores': [str(e)]}, status=500)

    @action(detail=False, methods=['post'], url_path='cargar_documentos_ficha', parser_classes=[MultiPartParser])
    def cargar_documentos_ficha(self, request):
        contexto = request.data.get("contexto")
        folder_id = request.data.get("folder_id")
        archivo = request.FILES.get("documento")

        if not folder_id or not archivo or not contexto:
            return Response({"detail": "Faltan datos"}, status=status.HTTP_400_BAD_REQUEST)

        if archivo.size == 0:
            return Response({"detail": "El archivo está vacío o la carga falló"}, status=status.HTTP_400_BAD_REQUEST)

        if contexto == "ficha":
            folder = get_object_or_404(T_DocumentFolder, id=folder_id)
            ruta = f'documentos/fichas/portafolio/{folder.ficha.id}/{archivo.name}'
        elif contexto == "aprendiz":
            folder = get_object_or_404(T_DocumentFolderAprendiz, id=folder_id)
            ruta = f'documentos/fichas/portafolio/aprendices/{folder.aprendiz.id}/{archivo.name}'
        else:
            return Response({"detail": "Contexto no válido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            extensiones_permitidas = ["pdf", "jpg", "jpeg", "png", "ppt", "pptx", "mp3", "mp4", "xls", "psc", "sql", "zip",
                                      "rar", "7z", "docx", "doc", "dotx", "dotm", "docm", "dot", "htm", "html", "mht", "mhtml",
                                      "xlt", "xltx", "xltm", "xml", "xlsb", "xlsx", "csv", "pptm", "pps", "ppsx", "ppsm",
                                      "pot", "potx", "potm", "sldx", "sldm", "pst", "ost", "msg", "eml", "mdb", "accdb",
                                      "accde", "accdt", "accdr", "one", "pub", "vsd", "vsdx", "xps", "txt", "gif", "svg",
                                      "avi", "wav", "flac",
                                      ]

            extension = archivo.name.split('.')[-1].lower()

            if extension not in extensiones_permitidas:
                return Response({
                    "message": f"{archivo.name}: tipo no permitido"
                }, status=status.HTTP_400_BAD_REQUEST)

            if extension in ['zip', 'rar', '7z']:
                max_size = 1000 * 1024 * 1024  # 1000MB
            else:
                max_size = 50 * 1024 * 1024  # 50MB

            if archivo.size > max_size:
                return Response({
                    "message": f"{archivo.name}: excede tamaño máximo "
                    f"({'1GB' if max_size > 50*1024*1024 else '50MB'})"
                }, status=status.HTTP_400_BAD_REQUEST)

            ruta_guardada = default_storage.save(ruta, archivo)

            size = (
                f"{archivo.size} B" if archivo.size < 1024 else
                f"{archivo.size // 1024} KB"
            )

            new_docu = T_docu.objects.create(
                nom=archivo.name,
                tipo=extension,
                tama=size,
                archi=ruta_guardada,
                priva="No",
                esta="Activo"
            )

            MODEL_MAP = {
                "ficha": T_DocumentFolder,
                "aprendiz": T_DocumentFolderAprendiz
            }
            model = MODEL_MAP[contexto]
            kwargs_extra = {"ficha": folder.ficha} if contexto == "ficha" else {
                "aprendiz": folder.aprendiz}

            with transaction.atomic():
                document_node = model.objects.create(
                    name=archivo.name,
                    parent=folder,
                    tipo="documento",
                    documento=new_docu,
                    **kwargs_extra
                )

                if contexto == "ficha":
                    related_id = document_node.ficha_id
                elif contexto == "aprendiz":
                    related_id = document_node.aprendiz_id
                else:
                    related_id = None

                extra_data = (
                    f"Se cargó el documento '{archivo.name}' "
                    f"en la carpeta {folder.id} "
                )

                AuditLog.objects.create(
                    user=request.user,
                    action="create",
                    content_type=ContentType.objects.get_for_model(
                        document_node),
                    object_id=document_node.id,
                    related_id=related_id,
                    related_type=contexto,
                    extra_data=extra_data
                )

            return Response({
                "message": "Documento cargado con éxito",
                "documento": {
                    "id": document_node.id,
                    "name": document_node.name,
                    "url": new_docu.archi.url,
                    "folder_id": folder.id,
                    "tipo": "documento"
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "message": "Error inesperado al cargar el documento",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['delete'], url_path='eliminar_documento_portafolio/(?P<doc_id>\d+)/(?P<contexto>[^/]+)')
    def eliminar_documento_portafolio(self, request, doc_id=None, contexto=None):
        if not doc_id or not contexto:
            return Response({"error": "Se requieren los parametros"}, status=status.HTTP_400_BAD_REQUEST)

        if contexto == "ficha":
            model = T_DocumentFolder
        elif contexto == "aprendiz":
            model = T_DocumentFolderAprendiz
        else:
            return Response({"detail": "Contexto no válido"}, status=status.HTTP_400_BAD_REQUEST)

        documento = get_object_or_404(model, id=doc_id)
        
        ancestros = documento.get_ancestors(include_self=False)
        prefijo = "PF" if contexto == "ficha" else "PA"

        ubicacion = " > ".join([
            f"{prefijo} {a.name}" if i == 0 else a.name
            for i, a in enumerate(ancestros)
        ])
        
        if contexto == "ficha":
            observacion = f"Documento asociado al portafolio de la ficha {documento.ficha.num}"
            ficha = documento.ficha
            related_type = "ficha"
            related_id = documento.ficha_id
        elif contexto == "aprendiz":
            observacion = f"Documento asociado al portafolio del aprendiz {documento.aprendiz.perfil.nom} con dni:{documento.aprendiz.perfil.dni}"
            ficha = documento.aprendiz.ficha
            related_type = "aprendiz"
            related_id = documento.aprendiz_id
        else:
            return Response({"detail": "Contexto no válido"}, status=status.HTTP_400_BAD_REQUEST)

        
        archivo_eliminado = T_porta_archi.objects.create(
          ficha = ficha,
          docu = documento.documento,
          eli_por = request.user,
          obser = observacion,
          ubi = ubicacion
        )
        
        if documento.documento:
          documento.documento = None

        documento.delete()

        extra_data = (
            f"Se elimino el documento '{archivo_eliminado.docu.nom}' "
            f"en la carpeta {documento.parent_id}"
        )

        AuditLog.objects.create(
            user=request.user,
            content_type=ContentType.objects.get_for_model(documento),
            object_id=documento.id,
            action="delete",
            related_id=related_id,
            related_type=related_type,
            extra_data=extra_data
        )

        return Response({"status": "success", "message": "Eliminado correctamente"}, status=200)

    @action(detail=False, methods=['get'], url_path='historial')
    def historial(self, request):
        contexto = request.query_params.get("contexto")
        obj_id = request.query_params.get("id")

        if not contexto or not obj_id:
            return Response({"error": "Se requiere contexto e id"}, status=400)

        try:
            obj_id = int(obj_id)
        except ValueError:
            return Response({"error": "ID invalido"}, status=400)

        if contexto == "ficha":
            modelo = T_DocumentFolder
        elif contexto == "aprendiz":
            modelo = T_DocumentFolderAprendiz
        elif contexto == "fichaG":
            modelo = T_ficha
        else:
            return Response({"error": "Contexto inválido"}, status=400)

        content_type = ContentType.objects.get_for_model(modelo)

        historial = AuditLog.objects.filter(
            content_type=content_type,
            related_id=obj_id
        ).order_by("-timestamp")

        data = [
            {
                "usuario": log.user.username if log.user else "Sistema",
                "accion": log.action,
                "detalle": log.extra_data,
                "fecha": localtime(log.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            }
            for log in historial
        ]
        return Response(data)

    @action(detail=False, methods=['get'], url_path='filtrar')
    def filtrar(self, request):
        estado = self.request.query_params.get('estados')
        instructor = self.request.query_params.get('instructores')
        programa = self.request.query_params.get('programas')
        search = request.GET.get("search[value]", "").strip()
        order_col_index = request.GET.get("order[0][column]")
        order_dir = request.GET.get("order[0][dir]")
        
        fichas = T_ficha.objects.all()

        mixin = PermisosMixin()
        mixin.modulo = "fichas"
        fichas = mixin.apply_permission_filters(fichas, request)
        acciones = mixin.get_permission_actions_for(request, "fichas")
        mixinP = PermisosMixin()
        accionesP = mixinP.get_permission_actions_for(request, "portafolios")


        perfil_logueado = T_perfil.objects.get(user=request.user)

        if perfil_logueado.rol == "instructor":
            ver_todos = acciones.get("verinstructor", False)
            
            if not ver_todos:
              instructor = T_instru.objects.get(perfil=perfil_logueado)
              fichas = fichas.filter(instru=instructor)

        elif perfil_logueado.rol == "gestor":
            gestor = T_gestor.objects.get(perfil=perfil_logueado)
            departamentos = T_gestor_depa.objects.filter(
                gestor=gestor
            ).values_list("depa__nom_departa", flat=True)

            fichas = fichas.filter(
                insti__muni__nom_departa__in=departamentos
            )

        if estado:
            fichas = fichas.filter(esta=estado)

        if instructor:
            fichas = fichas.filter(instru_id=instructor)

        if programa:
            fichas = fichas.filter(progra_id=programa)

        if search:
            fichas = fichas.filter(
                Q(num__icontains=search) |
                Q(esta__icontains=search) |
                Q(centro__nom__icontains=search) |
                Q(insti__nom__icontains=search) |
                Q(instru__perfil__dni__icontains=search) |
                Q(instru__perfil__nom__icontains=search) |
                Q(instru__perfil__apelli__icontains=search) |
                Q(progra__nom__icontains=search)
            )

        column_map = {
            "0": "num",
            "1": "grupo__num",
            "2": "esta",
            "3": "fecha_aper",
            "4": "centro__nom",
            "5": "insti__nom",
            "6": "instru__perfil__nom",
            "7": "num_apre_proce",
            "8": "progra__nom"
        }

        if order_col_index in column_map:
            field_name = column_map[order_col_index]
            if order_dir == "desc":
                field_name = f"-{field_name}"
            fichas = fichas.order_by(field_name)

        paginated = self.paginate_queryset(fichas)

        if paginated is not None:
            serialized = FichaFiltrarSerializer(paginated, many=True).data
            for d in serialized:
                d["can_edit"] = acciones.get("editar", False)
                d["can_delete"] = acciones.get("eliminar", False)
                d["can_view"] = acciones.get("ver", False)
                d["can_view_p"] = accionesP.get("ver", False)
            return self.get_paginated_response(serialized)

        # si no hay paginación
        serialized = FichaFiltrarSerializer(fichas, many=True).data
        for d in serialized:
            d["can_edit"] = acciones.get("editar", False)
            d["can_delete"] = acciones.get("eliminar", False)
            d["can_view"] = acciones.get("ver", False)
            d["can_view_p"] = accionesP.get("ver", False)
        return Response(serialized)

    @action(detail=False, methods=['get'], url_path='opciones-estados')
    def opciones_estados(self, request):
        perfil_logueado = T_perfil.objects.get(user=request.user)
        fichas = T_ficha.objects.filter(esta__isnull=False)

        if perfil_logueado.rol == "gestor":
            gestor = T_gestor.objects.get(perfil=perfil_logueado)
            departamentos = T_gestor_depa.objects.filter(
                gestor=gestor
            ).values_list('depa__nom_departa', flat=True)
            fichas = fichas.filter(
                insti__muni__nom_departa__nom_departa__in=departamentos
            )

        estados = fichas.distinct().values_list('esta', flat=True)
        return Response(list(estados))

    @action(detail=False, methods=['get'], url_path='opciones-instructores')
    def opciones_instructores(self, request):
        perfil_logueado = T_perfil.objects.get(user=request.user)

        # Si es instructor, devolver solo su id y nombre
        if perfil_logueado.rol == "instructor":
            try:
                instructor = T_instru.objects.get(perfil=perfil_logueado)
                return Response([{"id": instructor.id, "nombre": perfil_logueado.nom}])
            except T_instru.DoesNotExist:
                return Response([])

        fichas = T_ficha.objects.filter(instru__isnull=False)

        if perfil_logueado.rol == "gestor":
            gestor = T_gestor.objects.get(perfil=perfil_logueado)
            departamentos = T_gestor_depa.objects.filter(
                gestor=gestor
            ).values_list('depa__nom_departa', flat=True)
            fichas = fichas.filter(
                insti__muni__nom_departa__nom_departa__in=departamentos
            )

        instructores = fichas.distinct().values_list(
            'instru__id', 'instru__perfil__nom'
        )
        opciones = [{"id": None, "nombre": "Sin asignar"}] + [
            {"id": i[0], "nom": i[1]} for i in instructores
        ]
        return Response(opciones)

    @action(detail=False, methods=['get'], url_path='opciones-programas')
    def opciones_programas(self, request):
        perfil_logueado = T_perfil.objects.get(user=request.user)
        fichas = T_ficha.objects.filter(progra__isnull=False)

        if perfil_logueado.rol == "gestor":
            gestor = T_gestor.objects.get(perfil=perfil_logueado)
            departamentos = T_gestor_depa.objects.filter(
                gestor=gestor
            ).values_list('depa__nom_departa', flat=True)
            fichas = fichas.filter(
                insti__muni__nom_departa__nom_departa__in=departamentos
            )

        programas = fichas.distinct().values_list('progra__id', 'progra__nom')
        opciones = [{"id": p[0], "nom": p[1]} for p in programas]
        return Response(opciones)


class ProgramasViewSet(ModelViewSet):
    queryset = T_progra.objects.all()
    serializer_class = ProgramaSerializer
    permission_classes = [IsAuthenticated]


class FasesViewSet(ModelViewSet):
    queryset = T_fase.objects.all()
    serializer_class = FaseSerializer
    permission_classes = [IsAuthenticated]


class JuiciosViewSet(ModelViewSet):
    queryset = T_jui_eva_actu.objects.all()
    serializer_class = JuicioSerializer
    pagination_class = DataTablesPagination
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='filtrar')
    def filtrar(self, request):
        ficha_id = request.GET.get("id_ficha")
        search = request.GET.get("search[value]", "").strip()
        order_col_index = request.GET.get("order[0][column]")
        order_dir = request.GET.get("order[0][dir]")

        juicios = T_jui_eva_actu.objects.all()

        if ficha_id:
            juicios = juicios.filter(ficha__id=ficha_id)

        if search:
            juicios = juicios.filter(
                Q(eva__icontains=search) |
                Q(fecha_eva__icontains=search) |
                Q(apre__perfil__nom__icontains=search) |
                Q(apre__perfil__apelli__icontains=search) |
                Q(apre__perfil__dni__icontains=search) |
                Q(rap__cod__icontains=search) |
                Q(rap__nom__icontains=search)
            )

        column_map = {
            "0": "fecha_repor",
            "1": "apre__perfil__nom",
            "2": "rap__nom",
            "3": "eva",
            "4": "fecha_eva",
            "5": "instru__perfil__nom",
        }

        if order_col_index in column_map:
            field_name = column_map[order_col_index]
            if order_dir == "desc":
                field_name = f"-{field_name}"
            juicios = juicios.order_by(field_name)

        paginated = self.paginate_queryset(juicios)

        if paginated is not None:
            serializer = JuicioSerializer(paginated, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = JuicioSerializer(juicios, many=True)
        return Response(serializer.data)


class JuiciosHistoViewSet(ModelViewSet):
    queryset = T_jui_eva_diff
    serializer_class = JuicioHistoSerializer
    pagination_class = DataTablesPagination
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['GET'], url_path="filtrar")
    def filtrar(self, request):
        ficha_id = request.GET.get("ficha_id")
        search = request.GET.get("search[value]", "").strip()
        order_col_index = request.GET.get("order[0][column]")
        order_dir = request.GET.get("order[0][dir]")

        historial = T_jui_eva_diff.objects.all()

        if ficha_id:
            historial = historial.filter(ficha_id=ficha_id)

        if search:
            historial = historial.filter(
                Q(descri__icontains=search) |
                Q(fecha_diff__icontains=search) |
                Q(apre__perfil__dni__icontains=search) |
                Q(apre__perfil__nom__icontains=search) |
                Q(apre__perfil__apelli__icontains=search) |
                Q(tipo_cambi__icontains=search) |
                Q(jui__rap__cod__icontains=search)
            )

        column_map = {
            "0": "fecha_diff",
            "1": "apre__perfil__nom",
            "2": "descri",
            "3": "tipo_cambi",
            "4": "jui__rap__cod",
            "5": "instru__perfil__nom"
        }

        if order_col_index in column_map:
            field_name = column_map[order_col_index]
            if order_dir == "desc":
                field_name = f"-{field_name}"
            historial = historial.order_by(field_name)

        paginated = self.paginate_queryset(historial)

        if paginated is not None:
            serializer = JuicioHistoSerializer(paginated, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = JuicioHistoSerializer(historial, many=True)
        return Response(serializer.data)

class PortaArchiViewSet(ModelViewSet):
    queryset = T_porta_archi.objects.all().order_by('-eli_en')
    serializer_class = PortaArchiSerializer
    pagination_class = DataTablesPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = T_porta_archi.objects.all()
        ficha_id = self.request.query_params.get("id")
        if ficha_id:
            queryset = queryset.filter(ficha_id=ficha_id)
        return queryset