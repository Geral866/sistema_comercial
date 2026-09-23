from datetime import date
from django.db.models import Sum, F
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from ventas.models import Venta, DetalleVenta
from inventario.models import Inventario
from clientes.models import Cliente
from productos.models import Producto


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'reportes/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = date.today()

        ventas_hoy = Venta.objects.filter(fecha_venta__date=hoy)
        ventas_mes = Venta.objects.filter(
            fecha_venta__year=hoy.year, fecha_venta__month=hoy.month
        )

        context['total_ventas_hoy'] = ventas_hoy.aggregate(total=Sum('total'))['total'] or 0
        context['cantidad_ventas_hoy'] = ventas_hoy.count()
        context['total_ventas_mes'] = ventas_mes.aggregate(total=Sum('total'))['total'] or 0
        context['cantidad_ventas_mes'] = ventas_mes.count()

        context['total_clientes'] = Cliente.objects.count()
        context['total_productos'] = Producto.objects.filter(activo=True).count()

        # Productos más vendidos (por cantidad total vendida)
        context['top_productos'] = (
            DetalleVenta.objects
            .values(nombre=F('producto__nombre'))
            .annotate(total_vendido=Sum('cantidad'))
            .order_by('-total_vendido')[:5]
        )

        # Productos con stock bajo o agotado
        inventarios = Inventario.objects.select_related('producto')
        context['alertas_stock'] = [
            inv for inv in inventarios if inv.estado_stock in ('AGOTADO', 'BAJO')
        ]

        return context
    