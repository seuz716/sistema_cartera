from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from .models import Embarque, TipoCosto, CostoEmbarque

class EmbarqueModelTest(TestCase):
    def setUp(self):
        self.tipo_fle = TipoCosto.objects.create(nombre="Flete")

    def test_generar_numero_unico(self):
        """Verifica que el manager cree números únicos basados en la fecha."""
        e1 = Embarque.objects.crear_unico(conductor="Cesar")
        e2 = Embarque.objects.crear_unico(conductor="Juan")
        self.assertNotEqual(e1.numero, e2.numero)
        # Formato ddmmyyNN
        self.assertTrue(str(e1.numero).endswith("01"))
        self.assertTrue(str(e2.numero).endswith("02"))

    def test_costo_total_calculo(self):
        """Verifica la agregación de costos en el embarque."""
        emb = Embarque.objects.crear_unico(conductor="Test")
        CostoEmbarque.objects.create(
            embarque=emb, tipo=self.tipo_fle, precio_unitario=Decimal("100.00"), unidad="COP"
        )
        CostoEmbarque.objects.create(
            embarque=emb, tipo=self.tipo_fle, precio_unitario=Decimal("50.50"), unidad="COP"
        )
        # 100 + 51? aggregate sum gives 151? Let's use 150.5 in expected if fail again
        self.assertEqual(emb.costo_total, Decimal("150.5")) # Decimal fields sometimes strip trailing .00

    def test_calcular_monto_con_unidades(self):
        """Verifica el cálculo de monto basado en cantidad * precio."""
        emb = Embarque.objects.crear_unico(conductor="Test")
        costo = CostoEmbarque(
            embarque=emb, 
            tipo=self.tipo_fle, 
            cantidad=Decimal("10"), 
            precio_unitario=Decimal("5.00"),
            unidad="CAN"
        )
        costo.save()
        self.assertEqual(costo.monto, Decimal("50.00"))

class EmbarqueCRUDTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='staff', password='pass')
        self.client.login(username='staff', password='pass')
        self.tipo = TipoCosto.objects.create(nombre="Combustible")
        self.emb = Embarque.objects.crear_unico(conductor="Original")

    def test_list_view(self):
        response = self.client.get(reverse('embarques:lista'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Original")

    def test_create_view(self):
        data = {
            'fecha': '2024-03-01',
            'conductor': 'Nuevo Conductor',
            'vehiculo': 'Camion 1',
            'placa': 'ABC-123'
        }
        response = self.client.post(reverse('embarques:crear'), data)
        # EmbarqueCreateView hace redirect al detalle
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Embarque.objects.filter(conductor="Nuevo Conductor").exists())

    def test_update_view(self):
        data = {
            'fecha': self.emb.fecha.isoformat(),
            'conductor': 'Editado',
            'vehiculo': 'Moto',
            'placa': 'XYZ-999'
        }
        response = self.client.post(reverse('embarques:editar', args=[self.emb.pk]), data)
        self.assertEqual(response.status_code, 302)
        self.emb.refresh_from_db()
        self.assertEqual(self.emb.conductor, "Editado")

    def test_delete_view(self):
        response = self.client.post(reverse('embarques:eliminar', args=[self.emb.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Embarque.objects.filter(pk=self.emb.pk).exists())

    def test_costo_create_view(self):
        data = {
            'embarque': self.emb.pk, # El form tiene el campo hidden pero hay que enviarlo
            'tipo': self.tipo.pk,
            'cantidad': '1.00',
            'unidad': 'COP',
            'precio_unitario': '20000.00',
            'fecha': '2024-03-01',
            'descripcion': 'Transporte'
        }
        response = self.client.post(reverse('embarques:costo_crear', args=[self.emb.pk]), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.emb.costos.count(), 1)
