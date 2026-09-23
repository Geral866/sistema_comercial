from django.db import models
from clientes.models import Cliente
from productos.models import Producto


class Pedido(models.Model):
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADO', 'Confirmado'),
        ('CANCELADO', 'Cancelado'),
        ('COMPLETADO', 'Completado'),
    )

    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.PROTECT, 
        related_name="pedidos",
        verbose_name="Cliente"
    )
    fecha_pedido = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de pedido")
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE', verbose_name="Estado del pedido")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_pedido']
        
    @property
    def total(self):
        """Calcula el total sumando el subtotal de cada detalle asociado al pedido."""
        return sum(detalle.subtotal() for detalle in self.detalles.all())

    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.nombre}"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, 
        on_delete=models.CASCADE, 
        related_name="detalles",
        verbose_name="Pedido"
    )
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.PROTECT,
        verbose_name="Producto"
    )
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Precio unitario al momento del pedido")

    class Meta:
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedido"

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
    
  