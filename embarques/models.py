from django.db import models
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from django.core.validators import MinValueValidator

# -----------------------------
# MODELO: TipoCosto
# -----------------------------
class TipoCosto(models.Model):
    nombre = models.CharField(max_length=60, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Tipo de costo"
        verbose_name_plural = "Tipos de costo"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


# -----------------------------
# MODELO: Embarque
# -----------------------------
class EmbarqueManager(models.Manager):
    def crear_unico(self, fecha=None, **kwargs):
        from django.db import transaction, IntegrityError
        fecha = fecha or timezone.now().date()
        base = fecha.strftime("%d%m%y")
        for i in range(1, 100):
            numero = int(f"{base}{i:02d}")
            try:
                with transaction.atomic():
                    return self.create(numero=numero, fecha=fecha, **kwargs)
            except IntegrityError:
                continue
        raise RuntimeError("No se pudo generar número de embarque único para la fecha.")


class Embarque(models.Model):
    numero = models.PositiveBigIntegerField(unique=True, editable=False)
    fecha = models.DateField(default=timezone.now)
    conductor = models.CharField(max_length=100)
    vehiculo = models.CharField(max_length=50, blank=True, null=True)
    placa = models.CharField(max_length=20, blank=True, null=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    objects = EmbarqueManager()

    class Meta:
        ordering = ["-fecha", "-numero"]

    def generar_numero_si_no_tiene(self):
        if not self.numero:
            hoy = self.fecha.strftime("%d%m%y")
            consecutivo = Embarque.objects.filter(
                numero__startswith=int(hoy)
            ).count() + 1
            self.numero = int(f"{hoy}{consecutivo:02d}")

    def save(self, *args, **kwargs):
        if not self.numero:
            self.generar_numero_si_no_tiene()
        if self.conductor:
            self.conductor = self.conductor.strip().title()
        if self.vehiculo:
            self.vehiculo = self.vehiculo.strip().title()
        if self.placa:
            self.placa = self.placa.strip().upper()
        super().save(*args, **kwargs)

    @property
    def costo_total(self):
        return self.costos.aggregate(total=models.Sum("monto"))["total"] or Decimal("0.00")

    def __str__(self):
        return f"Embarque {self.numero} - {self.conductor}"


# -----------------------------
# MODELO: CostoEmbarque
# -----------------------------
UNIT_CHOICES = [
    ("UND", "Unidades"),
    ("KG", "Kilogramos"),
    ("CAN", "Canastillas"),
    ("LTS", "Litros"),
    ("COP", "Pesos (COP)"),
]

class CostoEmbarque(models.Model):
    embarque = models.ForeignKey(Embarque, on_delete=models.CASCADE, related_name="costos")
    tipo = models.ForeignKey(TipoCosto, on_delete=models.PROTECT, related_name="costos")
    descripcion = models.CharField(max_length=200, blank=True,
                                   help_text="Notas adicionales (opcional). No usar para tipificar el costo.")
    cantidad = models.DecimalField(max_digits=12, decimal_places=4, default=1,
                                   validators=[MinValueValidator(Decimal("0.00"))])
    unidad = models.CharField(max_length=10, choices=UNIT_CHOICES, default="COP")
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=4, default=0,
                                          validators=[MinValueValidator(Decimal("0.00"))])
    monto = models.DecimalField(max_digits=16, decimal_places=4, default=0,
                                validators=[MinValueValidator(Decimal("0.00"))])
    fecha = models.DateField(default=timezone.now)
    recibo = models.FileField(upload_to="embarques/%Y%m%d/costos/", blank=True, null=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha", "tipo__nombre"]
        verbose_name = "Costo de embarque"
        verbose_name_plural = "Costos de embarque"

    def calcular_monto(self):
        if self.unidad == "COP":
            return Decimal(self.precio_unitario).quantize(Decimal("1.00"), rounding=ROUND_HALF_UP)
        return (self.cantidad * self.precio_unitario).quantize(Decimal("1.00"), rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        self.monto = self.calcular_monto()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo.nombre} - {self.monto}"
