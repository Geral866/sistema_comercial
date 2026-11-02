from datetime import date, timedelta
from urllib.parse import urlencode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate, ExtractWeekDay
from django.http import HttpResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from ventas.models import Venta, DetalleVenta
from inventario.models import Inventario
from clientes.models import Cliente
from pedidos.models import Pedido

SUBTOTAL = ExpressionWrapper(
    F('cantidad') * F('precio_unitario'),
    output_field=DecimalField(max_digits=14, decimal_places=2),
)


def _cop(n):
    return '$' + f"{int(round(float(n or 0))):,}".replace(',', '.')


def _parse_fecha(valor):
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        return None


def _rango_fechas(request):
    hoy = timezone.localdate()
    rango = request.GET.get('rango', '30d')
    desde = _parse_fecha(request.GET.get('desde'))
    hasta = _parse_fecha(request.GET.get('hasta'))

    if desde and hasta:
        rango = 'personalizado'
    elif rango == 'hoy':
        desde = hasta = hoy
    elif rango == '7d':
        desde, hasta = hoy - timedelta(days=6), hoy
    elif rango == 'mes':
        desde, hasta = hoy.replace(day=1), hoy
    elif rango == 'anio':
        desde, hasta = hoy.replace(month=1, day=1), hoy
    else:
        rango = '30d'
        desde, hasta = hoy - timedelta(days=29), hoy

    if desde > hasta:
        desde, hasta = hasta, desde
    return rango, desde, hasta


def _kpis(desde, hasta):
    ventas = Venta.objects.filter(fecha_venta__date__range=(desde, hasta))
    agg = ventas.aggregate(total=Sum('total'), n=Count('id'))
    total = agg['total'] or 0
    n = agg['n'] or 0
    unidades = DetalleVenta.objects.filter(
        venta__fecha_venta__date__range=(desde, hasta)
    ).aggregate(u=Sum('cantidad'))['u'] or 0
    return {'total': total, 'n': n, 'unidades': unidades, 'ticket': (total / n) if n else 0}


def _variacion(actual, anterior):
    if not anterior:
        return None
    return round((float(actual) - float(anterior)) / float(anterior) * 100, 1)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'reportes/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rango, desde, hasta = _rango_fechas(self.request)

        dias = (hasta - desde).days + 1
        prev_hasta = desde - timedelta(days=1)
        prev_desde = prev_hasta - timedelta(days=dias - 1)

        actual = _kpis(desde, hasta)
        previo = _kpis(prev_desde, prev_hasta)

        ventas_qs = Venta.objects.filter(fecha_venta__date__range=(desde, hasta))
        detalles_qs = DetalleVenta.objects.filter(venta__fecha_venta__date__range=(desde, hasta))

        # Ventas por día (rellena con 0 los días sin ventas)
        por_dia = {
            r['dia']: r for r in ventas_qs.annotate(dia=TruncDate('fecha_venta'))
            .values('dia').annotate(total=Sum('total'), n=Count('id')).order_by('dia')
        }
        dias_labels, dias_total = [], []
        for i in range(dias):
            d = desde + timedelta(days=i)
            r = por_dia.get(d)
            dias_labels.append(d.strftime('%d/%m'))
            dias_total.append(float(r['total']) if r else 0)

        # Ventas por categoría
        cats = list(detalles_qs.values(nombre=F('producto__categoria__nombre'))
                    .annotate(total=Sum(SUBTOTAL)).order_by('-total'))

        # Top productos
        top = list(detalles_qs.values(nombre=F('producto__nombre'))
                   .annotate(unidades=Sum('cantidad'), ingresos=Sum(SUBTOTAL))
                   .order_by('-ingresos')[:8])

        # Métodos de pago
        etiquetas_pago = dict(Venta.METODO_PAGO_CHOICES)
        pagos = list(ventas_qs.values('metodo_pago')
                     .annotate(total=Sum('total')).order_by('-total'))

        # Ventas por día de la semana
        sem = {
            r['dow']: r for r in ventas_qs.annotate(dow=ExtractWeekDay('fecha_venta'))
            .values('dow').annotate(total=Sum('total')).order_by('dow')
        }
        nombres_sem = {2: 'Lun', 3: 'Mar', 4: 'Mié', 5: 'Jue', 6: 'Vie', 7: 'Sáb', 1: 'Dom'}
        orden_sem = [2, 3, 4, 5, 6, 7, 1]

        # Top clientes
        top_clientes = [
            {'nombre': r['nombre'], 'compras': r['compras'], 'total': _cop(r['total'])}
            for r in ventas_qs.values(nombre=F('cliente__nombre'))
            .annotate(total=Sum('total'), compras=Count('id')).order_by('-total')[:5]
        ]

        # Últimas ventas
        ultimas = [{
            'id': v.id,
            'fecha': timezone.localtime(v.fecha_venta).strftime('%d/%m/%Y %H:%M'),
            'cliente': v.cliente.nombre,
            'vendedor': v.vendedor.username,
            'metodo': v.get_metodo_pago_display(),
            'total': _cop(v.total),
        } for v in ventas_qs.select_related('cliente', 'vendedor').order_by('-fecha_venta')[:8]]

        # Inventario y operación (estado actual, no depende del rango)
        alertas_stock = [i for i in Inventario.objects.select_related('producto')
                         if i.estado_stock in ('AGOTADO', 'BAJO')]

        ctx.update({
            'rango': rango,
            'desde': desde.isoformat(),
            'hasta': hasta.isoformat(),
            'desde_txt': desde.strftime('%d/%m/%Y'),
            'hasta_txt': hasta.strftime('%d/%m/%Y'),
            'querystring': urlencode({'desde': desde.isoformat(), 'hasta': hasta.isoformat()}),
            'hay_ventas': actual['n'] > 0,
            'kpis': [
                {'titulo': 'Ventas totales', 'valor': _cop(actual['total']),
                 'var': _variacion(actual['total'], previo['total'])},
                {'titulo': 'Número de ventas', 'valor': actual['n'],
                 'var': _variacion(actual['n'], previo['n'])},
                {'titulo': 'Ticket promedio', 'valor': _cop(actual['ticket']),
                 'var': _variacion(actual['ticket'], previo['ticket'])},
                {'titulo': 'Unidades vendidas', 'valor': actual['unidades'],
                 'var': _variacion(actual['unidades'], previo['unidades'])},
            ],
            'clientes_nuevos': Cliente.objects.filter(fecha_registro__date__range=(desde, hasta)).count(),
            'pedidos_pendientes': Pedido.objects.filter(estado='PENDIENTE').count(),
            'alertas_stock': alertas_stock,
            'top_clientes': top_clientes,
            'ultimas': ultimas,
            'datos': {
                'dias': {'labels': dias_labels, 'total': dias_total},
                'categorias': {'labels': [c['nombre'] for c in cats],
                               'total': [float(c['total']) for c in cats]},
                'top': {'labels': [t['nombre'] for t in top],
                        'ingresos': [float(t['ingresos']) for t in top],
                        'unidades': [t['unidades'] for t in top]},
                'pagos': {'labels': [etiquetas_pago.get(p['metodo_pago'], p['metodo_pago']) for p in pagos],
                          'total': [float(p['total']) for p in pagos]},
                'semana': {'labels': [nombres_sem[d] for d in orden_sem],
                           'total': [float(sem[d]['total']) if d in sem else 0 for d in orden_sem]},
            },
        })
        return ctx


class ExportarVentasView(LoginRequiredMixin, View):
    def get(self, request):
        _, desde, hasta = _rango_fechas(request)

        detalles = (DetalleVenta.objects
                    .filter(venta__fecha_venta__date__range=(desde, hasta))
                    .select_related('venta__cliente', 'venta__vendedor', 'producto__categoria')
                    .order_by('venta__fecha_venta', 'venta_id'))

        wb = Workbook()
        ws = wb.active
        ws.title = 'Ventas'
        ws.append(['Fecha y hora', 'N° venta', 'Cliente', 'Ciudad', 'Categoría', 'Producto',
                   'Cantidad', 'Precio unitario', 'Subtotal', 'Método de pago', 'Vendedor'])
        for d in detalles:
            v = d.venta
            ws.append([
                timezone.localtime(v.fecha_venta).replace(tzinfo=None),
                v.id, v.cliente.nombre, v.cliente.ciudad or '',
                d.producto.categoria.nombre, d.producto.nombre,
                d.cantidad, float(d.precio_unitario), float(d.cantidad * d.precio_unitario),
                v.get_metodo_pago_display(), v.vendedor.username,
            ])
        for fila in ws.iter_rows(min_row=2):
            fila[0].number_format = 'DD/MM/YYYY HH:MM'
            fila[7].number_format = '"$"#,##0'
            fila[8].number_format = '"$"#,##0'
        self._estilizar(ws, [18, 10, 26, 16, 20, 30, 10, 16, 16, 22, 14])

        # Hoja 2: resumen por producto
        ws2 = wb.create_sheet('Resumen por producto')
        ws2.append(['Producto', 'Categoría', 'Unidades vendidas', 'Ingresos'])
        resumen = (detalles.values('producto__nombre', 'producto__categoria__nombre')
                   .annotate(u=Sum('cantidad'), ing=Sum(SUBTOTAL)).order_by('-ing'))
        for r in resumen:
            ws2.append([r['producto__nombre'], r['producto__categoria__nombre'], r['u'], float(r['ing'])])
        for fila in ws2.iter_rows(min_row=2):
            fila[3].number_format = '"$"#,##0'
        self._estilizar(ws2, [34, 22, 18, 18])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="ventas_{desde}_{hasta}.xlsx"'
        wb.save(response)
        return response

    @staticmethod
    def _estilizar(ws, anchos):
        for celda in ws[1]:
            celda.font = Font(bold=True, color='FFFFFF')
            celda.fill = PatternFill('solid', fgColor='23402C')
            celda.alignment = Alignment(horizontal='center', vertical='center')
        for i, ancho in enumerate(anchos, start=1):
            ws.column_dimensions[get_column_letter(i)].width = ancho
        ws.freeze_panes = 'A2'
        ws.auto_filter.ref = ws.dimensions
        
        
    