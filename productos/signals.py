from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Producto
from inventario.models import Inventario


@receiver(post_save, sender=Producto)
def crear_inventario_para_producto(sender, instance, created, **kwargs):
    if created:
        Inventario.objects.create(producto=instance, stock_actual=0)
        