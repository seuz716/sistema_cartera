from django.test import TestCase
from embarques.models import Vehiculo, Ruta, Transportador, Embarque
from ventas.forms import VentaForm
from clientes.models import Cliente
from django.utils import timezone

class LogisticsRefinementTest(TestCase):
    def setUp(self):
        self.vehiculo = Vehiculo.objects.create(placa="XYZ-789", marca="Chevrolet", modelo="NPR")
        self.ruta = Ruta.objects.create(nombre="Ruta Test", vehiculo_predeterminado=self.vehiculo)
        self.transportador = Transportador.objects.create(nombre="Juan Perez", documento="123")
        self.cliente = Cliente.objects.create(
            nombre="Test", 
            apellido="User", 
            numero_identificacion="999",
            email="test@example.com",
            tipo_persona="natural"
        )

    def test_ruta_vehiculo_predeterminado(self):
        """Verifica que la ruta tiene un vehículo asignado."""
        self.assertEqual(self.ruta.vehiculo_predeterminado.placa, "XYZ-789")

    def test_venta_form_embarque_required(self):
        """Verifica que el formulario de venta exige un embarque."""
        form = VentaForm(data={
            'cliente': self.cliente.pk,
            'fecha': timezone.now().date(),
            'factura': 'FAC-001',
            # No enviamos embarque
        })
        self.assertFalse(form.is_valid())
        self.assertIn('embarque', form.errors)

    def test_venta_form_filtered_embarque(self):
        """Verifica que solo se muestran embarques activos en la venta."""
        # Usamos save(full_clean=False) o similar para evitar validación de inventario en setup rápido de test
        e1 = Embarque(
            ruta=self.ruta, transportador=self.transportador, 
            vehiculo=self.vehiculo, fecha=timezone.now().date(),
            estado='FINALIZADO'
        )
        e1.save() # Sin full_clean() manual si no es necesario para este test específico
        
        e2 = Embarque(
            ruta=self.ruta, transportador=self.transportador, 
            vehiculo=self.vehiculo, fecha=timezone.now().date(),
            estado='EN_RUTA'
        )
        e2.save()
        
        form = VentaForm()
        queryset = form.fields['embarque'].queryset
        
        self.assertIn(e2, queryset)
        self.assertNotIn(e1, queryset)
