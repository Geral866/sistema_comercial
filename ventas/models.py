from django.db import models
from django.contrib.auth.models import User
from clientes.models import Cliente
from pedidos.models import Pedido
from productos.models import Producto


class Venta(models.Model):
    METODO_PAGO_CHOICES = (
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia / Nequi / Daviplata'),
        ('TARJETA', 'Tarjeta de Crédito / Débito'),
    )

    # FK opcional a Pedido (puede nacer de un pedido o ser venta directa en mostrador)
    pedido = models.OneToOneField(
        Pedido, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="venta",
        verbose_name="Pedido origen (Opcional)"
    )
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.PROTECT, 
        related_name="ventas",
        verbose_name="Cliente"
    )
    vendedor = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name="ventas_realizadas",
        verbose_name="Vendedor"
    )
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='EFECTIVO', verbose_name="Método de pago")
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Total facturado")
    fecha_venta = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y hora de venta")

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha_venta']

    def __str__(self):
        return f"Venta #{self.id} - Total: ${self.total}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(
        Venta, 
        on_delete=models.CASCADE, 
        related_name="detalles",
        verbose_name="Venta"
    )
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.PROTECT,
        verbose_name="Producto"
    )
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad vendida")
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Precio unitario")

    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Venta"

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
    