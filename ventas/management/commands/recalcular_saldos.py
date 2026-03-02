from django.core.management.base import BaseCommand
from ventas.models import Venta
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Recalcula subtotal, abonos y saldos de todas las ventas para asegurar consistencia.'

    def handle(self, *args, **options):
        ventas = Venta.objects.all()
        count = ventas.count()
        self.stdout.write(f"Iniciando recalculo de {count} ventas...")

        for venta in ventas:
            # Sumar detalles
            subtotal = venta.detalles.aggregate(total=Sum('precio_total'))['total'] or 0
            # Sumar pagos
            abonos = venta.pagos.aggregate(total=Sum('monto'))['total'] or 0
            
            venta.subtotal = subtotal
            venta.total = subtotal - venta.descuentos
            venta.total_con_flete = venta.total + venta.flete
            venta.abono = abonos
            venta.saldo = venta.total_con_flete - abonos
            
            if venta.saldo <= 0:
                venta.estado = "PAGADA"
            elif venta.abono > 0:
                venta.estado = "PARCIAL"
            else:
                venta.estado = "DEBE"
                
            venta.save()

        self.stdout.write(self.style.SUCCESS(f"Se recalcularon {count} ventas exitosamente."))
