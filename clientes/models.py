from django.db import models

class Cliente(models.Model):
    # Número único de identificación automático
    numero_unico = models.AutoField(primary_key=True)
    # Número de identificación proporcionado por el usuario
    numero_identificacion = models.CharField(max_length=50, unique=True)
    
    PERSONA_TIPO_CHOICES = [
        ('natural', 'Persona Natural'),
        ('juridica', 'Persona Jurídica'),
    ]
    tipo_persona = models.CharField(max_length=10, choices=PERSONA_TIPO_CHOICES)
    
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100)
    
    # Opciones de pago
    FORMA_PAGO_CHOICES = [
        ('contado', 'Contado'),
        ('credito_15', 'Crédito a 15 días'),
        ('credito_30', 'Crédito a 30 días'),
        ('credito_60', 'Crédito a 60 días'),
        ('otro', 'Otro'),
    ]
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_CHOICES)
    dias_credito = models.PositiveIntegerField(blank=True, null=True, help_text="Si selecciona 'Otro', especifique los días de crédito")
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)

    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def __str__(self):
        return self.nombre_completo()

