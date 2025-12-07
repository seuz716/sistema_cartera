# recoleccion/models.py
from django.db import models
from django.utils import timezone
from proveedores.models import Proveedor  # 👈 Importar el proveedor

class Ruta(models.Model):
    nombre = models.CharField(max_length=100)
    zona = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nombre


class Recoleccion(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name="recolecciones")
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE, related_name="recolecciones", null=True, blank=True)
    fecha = models.DateField(default=timezone.now)
    litros = models.DecimalField(max_digits=8, decimal_places=2)

    @property
    def quincena(self):
        return 1 if self.fecha.day <= 15 else 2

    def __str__(self):
        return f"{self.proveedor.nombre} - {self.fecha} - {self.litros} L"
