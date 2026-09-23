from django.db import models
from django.contrib.auth.models import User
from productos.models import Producto


class Inventario(models.Model):
    producto = models.OneToOneField(
        Producto, 
        on_delete=models.CASCADE, 
        related_name="inventario",
        verbose_name="Producto"
    )
    stock_actual = models.PositiveIntegerField(default=0, verbose_name="Stock actual")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    @property
    def estado_stock(self):
        if self.stock_actual <= 0:
            return 'AGOTADO'
        elif self.stock_actual <= self.producto.stock_minimo:
            return 'BAJO'
        return 'OK'

    class Meta:
        verbose_name = "Inventario"
        verbose_name_plural = "Inventarios"

    def __str__(self):
        return f"{self.producto.nombre} - Stock: {self.stock_actual}"


class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO = (
        ('ENTRADA', 'Entrada de Stock / Compra'),
        ('SALIDA', 'Salida de Stock / Venta'),
        ('AJUSTE', 'Ajuste Manual / Corrección'),
    )

    producto = models.ForeignKey(
        Producto, 
        on_delete=models.CASCADE, 
        related_name="movimientos",
        verbose_name="Producto"
    )
    usuario = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Usuario responsable"
    )
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO, verbose_name="Tipo de movimiento")
    cantidad = models.IntegerField(verbose_name="Cantidad")
    motivo = models.CharField(max_length=255, blank=True, null=True, verbose_name="Motivo / Observación")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del movimiento")

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo_movimiento} ({self.cantidad}) - {self.producto.nombre}"
    