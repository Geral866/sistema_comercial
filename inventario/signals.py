from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MovimientoInventario


@receiver(post_save, sender=MovimientoInventario)
def actualizar_stock_por_movimiento(sender, instance, created, **kwargs):
    if created and instance.tipo_movimiento in ('ENTRADA', 'AJUSTE'):
        inventario = instance.producto.inventario
        inventario.stock_actual += instance.cantidad
        inventario.save()
        
        