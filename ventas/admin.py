from django.contrib import admin
from .models import Venta, DetalleVenta


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'vendedor', 'metodo_pago', 'total', 'fecha_venta')
    list_filter = ('metodo_pago',)
    search_fields = ('cliente__nombre',)
    inlines = [DetalleVentaInline]
    readonly_fields = ('fecha_venta',)
    