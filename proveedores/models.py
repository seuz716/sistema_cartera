from django.db import models


class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    identificacion = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    ruta = models.ForeignKey("recoleccion.Ruta", on_delete=models.SET_NULL, null=True, blank=True)
    rut = models.FileField(upload_to='ruts/', blank=True, null=True)  # Para subir el RUT

    def __str__(self):
        return self.nombre
