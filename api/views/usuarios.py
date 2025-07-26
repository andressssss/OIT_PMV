from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from django.core.validators import validate_email
from django.core.files.storage import default_storage
from datetime import datetime
from io import TextIOWrapper
from django.db import transaction
from django.forms import ValidationError
from django.utils import timezone
from django.db.models import Subquery, OuterRef, Exists
import csv
from django.contrib.auth.models import User
from commons.models import T_perfil, T_centro_forma, T_departa, T_munici, T_insti_edu, T_apre, T_ficha, T_prematri_docu, T_repre_legal
from api.serializers.usuarios import PerfilSerializer, DepartamentoSerializer, InstitucionSerializer, MunicipioSerializer, CentroFormacionSerializer, AprendizSerializer
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from matricula.scripts.cargar_tree_apre import crear_datos_prueba_aprendiz
from commons.permisos import DenegarConsulta

class PerfilPagination(PageNumberPagination):
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


class PerfilViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = T_perfil.objects.all()
    serializer_class = PerfilSerializer
    pagination_class = PerfilPagination

    @action(detail=False, methods=['get'], url_path='filtrar')
    def filtrar(self, request):
        rol = request.GET.getlist('rol', [])
        tipo_dni = request.GET.getlist('tipo_dni', [])
        search = request.GET.get('search[value]', '').strip()

        perfiles = T_perfil.objects.all()

        if rol:
            perfiles = perfiles.filter(rol__in=rol)

        if tipo_dni:
            perfiles = perfiles.filter(tipo_dni__in=tipo_dni)

        if search:
            perfiles = perfiles.filter(
                Q(user__username__icontains=search) |
                Q(nom__icontains=search) |
                Q(apelli__icontains=search) |
                Q(mail__icontains=search) |
                Q(rol__icontains=search) |
                Q(dni__icontains=search)
            )

        paginated = self.paginate_queryset(perfiles)
        serializer = PerfilSerializer(paginated, many=True)
        return self.get_paginated_response(serializer.data)


class CentroFormacionViewSet(ModelViewSet):
    queryset = T_centro_forma.objects.all()
    serializer_class = CentroFormacionSerializer
    permission_classes = [IsAuthenticated]


class DepartamentoViewSet(ModelViewSet):
    queryset = T_departa.objects.all()
    serializer_class = DepartamentoSerializer
    permission_classes = [IsAuthenticated]


class MunicipioViewSet(ModelViewSet):
    queryset = T_munici.objects.all()
    serializer_class = MunicipioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        departamento_id = self.request.query_params.get('departamento')
        if departamento_id:
            queryset = queryset.filter(nom_departa_id=departamento_id)
        return queryset


class InstitucionViewSet(ModelViewSet):
    queryset = T_insti_edu.objects.all()
    serializer_class = InstitucionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        municipio_id = self.request.query_params.get('municipio')
        if municipio_id:
            queryset = queryset.filter(muni_id=municipio_id)
        return queryset


class AprendizViewSet(ModelViewSet):
    queryset = T_apre.objects.all()
    serializer_class = AprendizSerializer
    permission_classes = [IsAuthenticated, DenegarConsulta]

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        return Response({
            "message": "Aprendiz actualizado correctamente",
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='validar_dni')
    def validar_dni(self, request):
        dni = request.query_params.get('dni')
        if not dni:
            return Response({'message': 'DNI no proporcionado'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            perfil = T_perfil.objects.get(dni=dni)
        except T_perfil.DoesNotExist:
            return Response({"existe": False, "message": "El aprendiz no existe en el sistema"})

        try:
            aprendiz = T_apre.objects.get(perfil=perfil)
        except T_apre.DoesNotExist:
            return Response({"existe": False, "message": "El aprendiz no existe en el sistema"})

        if aprendiz.ficha == None:
            return Response({"existe": True, "asociado": False, "message": "El aprendiz existe pero no esta asociado a ninguna ficha"})

        if aprendiz.ficha != None:
            return Response({
                "existe": True,
                "asociado": True,
                "message": f"El aprendiz esta asociado a la ficha {aprendiz.ficha.num}"
            })

    @action(detail=True, methods=['post'], url_path='asociar_ficha')
    def asociar_ficha(self, request, pk=None):
        ficha_id = request.query_params.get('ficha_id')

        if not ficha_id:
            return Response({'detail': 'El parámetro ficha_id es obligatorio'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            aprendiz = T_apre.objects.get(perfil__dni=pk)
            ficha = T_ficha.objects.get(pk=ficha_id)
            aprendiz.ficha = ficha
            aprendiz.save()
            return Response({'message': 'ficha asociada correctamente'}, status=status.HTTP_200_OK)
        except T_ficha.DoesNotExist:
            return Response({'detail': 'Ficha no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='crear_un_apre', parser_classes=[MultiPartParser])
    def crear_un_aprendiz_csv(self, request):
        archivo = request.FILES.get('archivo')
        ficha_id = request.POST.get('ficha_id')

        if not archivo or not ficha_id:
            return Response({"message": "Falta el archivo CSV o ficha_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lector = list(csv.DictReader(TextIOWrapper(
                archivo.file, encoding='utf-8-sig'), delimiter=';'))
        except Exception as e:
            return Response({"message": "Archivo inválido", "errores": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)

        if len(lector) != 1:
            return Response({"message": "El archivo debe contener solo una fila de datos"}, status=400)

        fila = lector[0]
        errores = []
        resumen = {"insertado": 0}
        documentos_matricula = [
            'Documento de Identidad del aprendiz',
            'Registro civil',
            'Certificado de Afiliación de salud',
            'Formato de Tratamiento de Datos del Menor de Edad',
            'Compromiso del Aprendiz',
        ]

        try:
            with transaction.atomic():
                required_fields = ['nom', 'apelli', 'email',
                                   'tipo_dni', 'dni', 'tele', 'gene']
                missing = [field for field in required_fields if not fila.get(
                    field, '').strip()]
                if missing:
                    raise ValidationError(
                        f"Campos faltantes: {', '.join(missing)}")

                dni = fila['dni'].strip()
                email = fila['email'].strip()

                if T_perfil.objects.filter(dni=dni).exists():
                    raise ValidationError(
                        f"El DNI '{dni}' ya está registrado.")
                if T_perfil.objects.filter(mail=email).exists():
                    raise ValidationError(
                        f"El correo '{email}' ya está registrado.")

                try:
                    ficha = T_ficha.objects.get(id=ficha_id)
                except T_ficha.DoesNotExist:
                    raise ValidationError(
                        f"La ficha con ID {ficha_id} no existe.")

                fecha_naci = fila.get('fecha_naci')
                fecha_naci = datetime.strptime(
                    fecha_naci.strip(), '%d/%m/%Y').date() if fecha_naci else None

                base_username = (fila['nom'][:3] + fila['apelli'][:3]).lower()
                username = base_username
                contador = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{contador}"
                    contador += 1

                user = User.objects.create_user(
                    username=username, password=str(dni), email=email)

                perfil = T_perfil.objects.create(
                    user=user,
                    nom=fila['nom'],
                    apelli=fila['apelli'],
                    tipo_dni=fila['tipo_dni'],
                    dni=dni,
                    tele=fila['tele'],
                    dire=fila.get('dire', ''),
                    mail=email,
                    gene=fila['gene'],
                    fecha_naci=fecha_naci,
                    rol='aprendiz'
                )
                perfil.full_clean()

                # Representante legal (opcional)
                repre = None
                dni_repre = fila.get('dni_repre', '').strip()
                if dni_repre:
                    mail_repre = fila.get('mail_repre', '').strip()
                    try:
                        validate_email(mail_repre)
                    except ValidationError:
                        raise ValidationError(
                            f"Correo de representante inválido: {mail_repre}")

                    repre = T_repre_legal.objects.filter(dni=dni_repre).first()
                    if not repre:
                        repre = T_repre_legal(
                            nom=fila.get('nom_repre', ''),
                            dni=dni_repre,
                            tele=fila.get('tele_repre', ''),
                            dire=fila.get('dire_repre', ''),
                            mail=mail_repre,
                            paren=fila.get('parentezco', '')
                        )
                        repre.full_clean()
                        repre.save()

                aprendiz = T_apre.objects.create(
                    cod="z",
                    esta="activo",
                    perfil=perfil,
                    grupo=ficha.grupo,
                    ficha=ficha,
                    usu_crea=request.user,
                    esta_docu="Pendiente",
                    repre_legal=repre
                )
                aprendiz.full_clean()

                for doc in documentos_matricula:
                    T_prematri_docu.objects.create(
                        nom=doc,
                        apren=aprendiz,
                        esta="Pendiente",
                        vali="0"
                    )

                crear_datos_prueba_aprendiz(aprendiz.id)
                resumen['insertado'] = 1

                ficha.num_apre_pendi_regi = T_apre.objects.filter(
                    ficha=ficha).count()
                ficha.num_apre_proce = ficha.num_apre_pendi_regi
                ficha.save()

            return Response({'message': 'Aprendiz creado correctamente.', 'resumen': resumen}, status=201)

        except Exception as e:
            return Response({"message": "Error al crear aprendiz", "errores": [str(e)]}, status=400)
