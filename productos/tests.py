from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Producto

class ProductoModelTest(TestCase):
    def test_creacion_producto_decimales(self):
        """Validar que el producto guarde correctamente los decimales."""
        p = Producto.objects.create(
            nombre="Queso Crema",
            precio_unitario=Decimal("12500.50"),
            stock_actual=Decimal("100.25"),
            unidad_medida="KG"
        )
        self.assertEqual(p.precio_unitario, Decimal("12500.50"))
        self.assertEqual(p.stock_actual, Decimal("100.25"))

    def test_precio_negativo_no_permitido(self):
        """Validar que el validador impida precios negativos."""
        from django.core.exceptions import ValidationError
        p = Producto(
            nombre="Error",
            precio_unitario=Decimal("-10.00")
        )
        with self.assertRaises(ValidationError):
            p.full_clean()

class ProductoCRUDTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='staff', password='pass')
        self.client.login(username='staff', password='pass')
        self.producto = Producto.objects.create(
            nombre="Cuajada",
            precio_unitario=Decimal("5000.00"),
            stock_actual=Decimal("10.00")
        )

    def test_listado_productos(self):
        response = self.client.get(reverse('productos:lista'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cuajada")

    def test_crear_producto_con_imagen(self):
        # Crear una pequeña imagen ficticia
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        fake_img = SimpleUploadedFile("test.gif", small_gif, content_type="image/gif")
        
        data = {
            'nombre': "Nuevo Queso",
            'precio_unitario': "15000.00",
            'stock_actual': "50.00",
            'unidad_medida': "UND",
            'imagen': fake_img,
            'activo': True
        }
        response = self.client.post(reverse('productos:crear'), data)
        self.assertEqual(response.status_code, 302)
        nuevo = Producto.objects.get(nombre="Nuevo Queso")
        self.assertTrue(nuevo.imagen.name.endswith(".gif"))

    def test_editar_producto_precio(self):
        data = {
            'nombre': "Cuajada Especial",
            'precio_unitario': "5500.00",
            'stock_actual': "10.00",
            'unidad_medida': "UND",
            'activo': True
        }
        response = self.client.post(reverse('productos:editar', args=[self.producto.pk]), data)
        self.assertEqual(response.status_code, 302)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.nombre, "Cuajada Especial")
        self.assertEqual(self.producto.precio_unitario, Decimal("5500.00"))

    def test_eliminar_producto(self):
        response = self.client.post(reverse('productos:eliminar', args=[self.producto.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Producto.objects.filter(pk=self.producto.pk).exists())
