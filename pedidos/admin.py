from django.contrib import admin
from .models import Pedido, DetallePedido


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'estado', 'fecha_pedido', 'total')
    list_filter = ('estado',)
    search_fields = ('cliente__nombre',)
    inlines = [DetallePedidoInline]

    def total(self, obj):
        return obj.total
    total.short_description = 'Total'
    