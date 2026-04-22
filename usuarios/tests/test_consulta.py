from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth.models import User
from commons.models import T_perfil, T_consulta
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
