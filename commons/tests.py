from django.test import TestCase
from .models import *
from django.contrib.auth import get_user_model

User = get_user_model()

class PortaArchiModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="1234")
        
        self.ficha = T_ficha.objects.create(nom="Ficha 001")
        
        self.docu = T_docu.objects.create(nom="Doc tester")
        
        self.archivo = T_porta_archi.objects.create(
            ficha = self.ficha,
            docu= self.docu,
            eli_por=self.user,
            obser="Documento obsoleto",
            ubi="/tmp/doc.pdf"
        )

    def test_creacion_archivo(self):
        self.assertEqual(T_porta_archi.objects.count(), 1)

        self.assertEqual(self.archivo.ficha.nombre, "Ficha 001")
        self.assertEqual(self.archivo.docu.nombre, "Doc tester")

        self.assertEqual(self.archivo.eli_por.username, "tester")

        self.assertEqual(self.archivo.obser, "Documento obsoleto")

    def test_str(self):
        self.assertIn("Archivo eliminado", str(self.archivo))
