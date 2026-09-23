from django.contrib import admin
from .models import Inventario, MovimientoInventario


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'stock_actual', 'fecha_actualizacion')
    search_fields = ('producto__nombre',)


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo_movimiento', 'cantidad', 'usuario', 'fecha')
    list_filter = ('tipo_movimiento',)
    search_fields = ('producto__nombre',)
    readonly_fields = ('fecha',)
    