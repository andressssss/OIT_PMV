import json
from django.test import TestCase, Client
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.urls import reverse
from commons.models import T_perfil, T_consulta, T_admin, T_permi
from usuarios.forms import ConsultaForm


class T_consultaModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testcon', password='1234')
        self.perfil = T_perfil.objects.create(
            user=self.user, nom='Ana', apelli='Lopez',
            tipo_dni='CC', dni=123456789, tele='3001234567',
            dire='Calle 1', mail='ana@test.com', gene='M',
            fecha_naci='1990-01-01', rol='consulta'
        )

    def test_crear_consulta(self):
        consulta = T_consulta.objects.create(
            perfil=self.perfil,
            area='sistemas',
            nivel_acceso='basico',
            esta='activo'
        )
        self.assertEqual(consulta.perfil, self.perfil)
        self.assertEqual(consulta.area, 'sistemas')
        self.assertEqual(consulta.nivel_acceso, 'basico')
        self.assertEqual(consulta.esta, 'activo')

    def test_str_consulta(self):
        consulta = T_consulta.objects.create(
            perfil=self.perfil, area='contable',
            nivel_acceso='intermedio', esta='activo'
        )
        self.assertIn('Ana', str(consulta))

    def test_perfil_unicidad(self):
        T_consulta.objects.create(perfil=self.perfil, area='sistemas', nivel_acceso='basico', esta='activo')
        with self.assertRaises(IntegrityError):
            T_consulta.objects.create(perfil=self.perfil, area='contable', nivel_acceso='avanzado', esta='activo')


class ConsultaFormTest(TestCase):
    def test_form_valid(self):
        form = ConsultaForm(data={
            'area': 'sistemas',
            'nivel_acceso': 'basico',
            'esta': 'activo',
        })
        self.assertTrue(form.is_valid())

    def test_form_invalid_missing_area(self):
        form = ConsultaForm(data={'nivel_acceso': 'basico', 'esta': 'activo'})
        self.assertFalse(form.is_valid())
        self.assertIn('area', form.errors)


class ConsultaViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        admin_user = User.objects.create_user(username='admin1', password='pass')
        perfil_admin = T_perfil.objects.create(
            user=admin_user, nom='Admin', apelli='Test',
            tipo_dni='CC', dni=999999999, tele='3000000000',
            dire='Calle Admin', mail='admin@test.com', gene='H',
            fecha_naci='1985-01-01', rol='admin'
        )
        T_admin.objects.create(perfil=perfil_admin, area='sistemas', esta='activo')
        T_permi.objects.create(perfil=perfil_admin, modu='consultas', acci='ver', filtro=None)
        T_permi.objects.create(perfil=perfil_admin, modu='consultas', acci='editar', filtro=None)
        self.client.login(username='admin1', password='pass')

    def test_lista_consultas_returns_200(self):
        response = self.client.get(reverse('consultas'))
        self.assertEqual(response.status_code, 200)

    def test_crear_consulta_post(self):
        response = self.client.post(reverse('api_crear_consulta'), {
            'nom': 'Carlos', 'apelli': 'Ruiz', 'tipo_dni': 'CC',
            'dni': '111222333', 'tele': '3101234567', 'dire': 'Cra 5',
            'mail': 'carlos@test.com', 'gene': 'H', 'fecha_naci': '1995-06-15',
            'area': 'contable', 'nivel_acceso': 'basico', 'esta': 'activo',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
