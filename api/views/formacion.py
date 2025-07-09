from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from datetime import datetime
from io import TextIOWrapper
from django.db import transaction
from django.forms import ValidationError
from django.utils import timezone 
from django.db.models import Subquery, OuterRef, Exists
import csv

from api.serializers.formacion import RAPSerializer, CompetenciaSerializer, FichaSerializer, BaseRapsSerializer
from commons.models import T_raps, T_compe, T_ficha, T_prematri_docu, T_DocumentFolder,T_apre, T_centro_forma, T_progra, T_insti_edu, T_compe_progra, T_raps_ficha, T_perfil, T_instru, T_gestor_grupo, T_grupo, T_fase_ficha, T_gestor_depa, T_gestor
from django.contrib.auth.models import User

from matricula.scripts.cargar_tree import crear_datos_prueba 
from matricula.scripts.cargar_tree_apre import crear_datos_prueba_aprendiz

import logging

logger = logging.getLogger(__name__)

class RapsViewSet(ModelViewSet):
    queryset = T_raps.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return RAPSerializer if self.action in ['list', 'retrieve'] else BaseRapsSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                'status': 'success',
                'message': 'RAP creado correctamente',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'message': 'Formulario inválido',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        rap_id = instance.id
        rap_nom = instance.nom

        instance.fase.clear()
        instance.delete()

        return Response({
            'status': 'success',
            'message': f'RAP {rap_nom} eliminado correctamente'
        }, status=status.HTTP_200_OK)

class CompetenciasViewSet(ModelViewSet):
    serializer_class = CompetenciaSerializer
    queryset = T_compe.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        programa_id = self.request.query_params.get('programa')
        logger.warning(f"programa_id recibido: {programa_id}")
        if programa_id:
            queryset = queryset.filter(progra__id=programa_id)
        return queryset

class FichasViewSet(ModelViewSet):
    queryset = T_ficha.objects.all()
    serializer_class = FichaSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    @action(detail=False, methods=['get'], url_path='por_programa/(?P<programa_id>[^/.]+)')
    def fichas_por_programa(self, request, programa_id=None):
        fichas = self.get_queryset().filter(progra = programa_id)
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
            name = nombre,
            parent_id = parent_id,
            ficha = ficha,
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
            lector = csv.DictReader(TextIOWrapper(archivo.file, encoding='utf-8-sig'), delimiter=';')
        except Exception as e:
            return Response({"message": "Archivo invalido", "errores": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
        
        errores = []
        resumen = {'insertados': 0}

        try:
            with transaction.atomic():
                for i, fila in enumerate(lector, start=2):
                    required_fields = ['num_ficha', 'fase', 'cod_centro_forma', 'dane_insti', 'nombre_progra', 'cedula_instru']
                    missing = [field for field in required_fields if not fila.get(field, '').strip()]
                    if missing:
                        raise ValidationError(f"Fila {i}: Campos faltantes: {', '.join(missing)}")

                    num_ficha = fila['num_ficha'].strip()
                    fase_actual = fila['fase'].strip()

                    # 🚨 Validaciones críticas — si fallan, se detiene TODO
                    try:
                        centro = T_centro_forma.objects.get(cod=fila['cod_centro_forma'])
                    except T_centro_forma.DoesNotExist:
                        raise ValidationError(f"Fila {i}: Centro de formación '{fila['cod_centro_forma']}' no encontrado")

                    try:
                        institucion = T_insti_edu.objects.get(dane=fila['dane_insti'])
                    except T_insti_edu.DoesNotExist:
                        raise ValidationError(f"Fila {i}: Institución con DANE '{fila['dane_insti']}' no encontrada")

                    try:
                        programa = T_progra.objects.get(nom=fila['nombre_progra'])
                    except T_progra.DoesNotExist:
                        raise ValidationError(f"Fila {i}: Programa '{fila['nombre_progra']}' no encontrado")

                    # Instructor opcional
                    cedula = fila['cedula_instru'].strip()
                    if cedula in ['0', '']:
                        instructor = None
                    else:
                        try:
                            perfil_instru = T_perfil.objects.get(dni=cedula)
                            instructor = T_instru.objects.get(perfil=perfil_instru)
                        except (T_perfil.DoesNotExist, T_instru.DoesNotExist):
                            raise ValidationError(f"Fila {i}: Instructor con cédula '{cedula}' no encontrado")

                    if T_ficha.objects.filter(num=num_ficha).exists():
                        raise ValidationError(f"Fila {i}: La ficha {num_ficha} ya existe.")

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
                    gestor_depa = T_gestor_depa.objects.filter(depa=departamento).select_related('gestor').first()
                    gestor = gestor_depa.gestor if gestor_depa else T_gestor.objects.get(pk=1)

                    T_gestor_grupo.objects.create(
                        fecha_crea=timezone.now(),
                        autor=request.user,
                        gestor=gestor,
                        grupo=grupo
                    )

                    for f in range(1, int(fase_actual)):
                        T_fase_ficha.objects.create(fase_id=f, ficha=ficha, fecha_ini=timezone.now(), instru=instructor, vige=0)
                    T_fase_ficha.objects.create(fase_id=fase_actual, ficha=ficha, fecha_ini=timezone.now(), instru=instructor, vige=1)

                    compe_ids = T_compe_progra.objects.filter(progra=ficha.progra).values('compe_id')
                    raps = T_raps.objects.filter(compe__in=Subquery(compe_ids))

                    raps_ficha_objs = [
                        T_raps_ficha(ficha=ficha, rap=rap, fase=rap_fase.fase)
                        for rap in raps
                        for rap_fase in rap.t_raps_fase_set.all()
                    ]

                    T_raps_ficha.objects.bulk_create(raps_ficha_objs)

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
            return Response({"message": "No se envio ningun archivo"}, status = status.HTTP_400_BAD_REQUEST)

        try:
            lector = csv.DictReader(TextIOWrapper(archivo.file, encoding='utf-8-sig'), delimiter=';')
        except Exception as e:
            return Response({"message": "Archivo invalido", "errores": [str(e)]}, status= status.HTTP_400_BAD_REQUEST)
        
        errores = []
        resumen = {'insertados': 0}


        documentos_matricula = [
            'Documento de Identidad del aprendiz',
            'Registro civil',
            'Certificado de Afiliación de salud',
            'Formato de Tratamiento de Datos del Menor de Edad',
            'Compromiso del Aprendiz',
        ]

        try:
            with transaction.atomic():
                for i, fila in enumerate(lector, start=2):
                    try:
                        required_fields = ['nom', 'apelli', 'email', 'tipo_dni', 'dni', 'tele', 'gene', 'fecha_naci', 'num_ficha']
                        missing = [field for field in required_fields if not fila.get(field, '').strip()]
                        if missing:
                            raise ValidationError(f"Campos faltantes: {', '.join(missing)}")
                        
                        dni = fila['dni'].strip()
                        ficha_num = fila['num_ficha'].strip()

                        if not T_ficha.objects.filter(num= ficha_num).exists():
                            raise ValidationError(f"La ficha {ficha_num} no existe!.")
                        
                        ficha = T_ficha.objects.get(num=ficha_num)

                        fecha_naci = datetime.strptime(fila['fecha_naci'].strip(), '%d/%m/%Y').date()
                        base_username = (fila['nom'][:3] + fila['apelli'][:3]).lower()
                        username = base_username
                        i = 1
                        while User.objects.filter(username=username).exists():
                            username = f"{base_username}{i}"
                            i += 1

                        new_user = User.objects.create_user(
                            username = username,
                            password= str(dni),
                            email=fila['email']
                        )

                        new_perfil = T_perfil.objects.create(
                            user = new_user,
                            nom= fila['nom'],
                            apelli = fila['apelli'],
                            tipo_dni=fila['tipo_dni'],
                            dni=dni,
                            tele=fila['tele'],
                            dire=fila['dire'],
                            gene=fila['gene'],
                            mail=fila['email'],
                            fecha_naci=fecha_naci,
                            rol="aprendiz"
                        )
                        new_perfil.full_clean()

                        new_aprendiz = T_apre.objects.create(
                            cod="z",
                            esta="activo",
                            perfil=new_perfil,
                            grupo = ficha.grupo,
                            ficha= ficha,
                            usu_crea=request.user,
                            esta_docu = "Pendiente"
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
                aprendices_totales = T_apre.objects.filter(ficha = ficha).count()
                ficha.num_apre_pendi_regi = aprendices_totales
                ficha.num_apre_proce = aprendices_totales
                ficha.save()
            if errores:
                return Response({'message': 'Errores al importar.', 'errores': errores}, status=400)

            return Response({'message': 'Aprendices importados correctamente.', 'resumen': resumen}, status=201)

        except Exception as e:
            return Response({'message': 'Error crítico', 'errores': [str(e)]}, status=500)