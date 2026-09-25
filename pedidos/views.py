from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DeleteView, ListView

from inventario.models import MovimientoInventario
from ventas.models import DetalleVenta, Venta
from .forms import PedidoForm
from .models import DetallePedido, Pedido

DetallePedidoFormSet = inlineformset_factory(
    Pedido, DetallePedido,
    fields=['producto', 'cantidad', 'precio_unitario'],
    extra=1, can_delete=True
)


class PedidoListView(LoginRequiredMixin, ListView):
    model = Pedido
    template_name = 'pedidos/pedido_list.html'
    context_object_name = 'pedidos'
    paginate_by = 10

    def get_queryset(self):
        return Pedido.objects.select_related('cliente').order_by('-fecha_pedido')


class PedidoCreateView(LoginRequiredMixin, View):
    template_name = 'pedidos/pedido_form.html'

    def get(self, request):
        form = PedidoForm()
        formset = DetallePedidoFormSet()
        return render(request, self.template_name, {'form': form, 'formset': formset})

    def post(self, request):
        form = PedidoForm(request.POST)
        formset = DetallePedidoFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            detalles_validos = [f for f in formset if f.cleaned_data and not f.cleaned_data.get('DELETE')]
            if not detalles_validos:
                messages.error(request, "El pedido debe tener al menos un producto.")
                return render(request, self.template_name, {'form': form, 'formset': formset})

            pedido = form.save()
            formset.instance = pedido
            formset.save()
            messages.success(request, "Pedido creado correctamente.")
            return redirect('pedidos:lista')
        return render(request, self.template_name, {'form': form, 'formset': formset})


class PedidoUpdateView(LoginRequiredMixin, View):
    template_name = 'pedidos/pedido_form.html'

    def get(self, request, pk):
        pedido = get_object_or_404(Pedido, pk=pk)
        form = PedidoForm(instance=pedido)
        formset = DetallePedidoFormSet(instance=pedido)
        return render(request, self.template_name, {'form': form, 'formset': formset, 'object': pedido})

    def post(self, request, pk):
        pedido = get_object_or_404(Pedido, pk=pk)
        form = PedidoForm(request.POST, instance=pedido)
        formset = DetallePedidoFormSet(request.POST, instance=pedido)
        if form.is_valid() and formset.is_valid():
            pedido = form.save()
            formset.save()
            messages.success(request, "Pedido actualizado correctamente.")
            return redirect('pedidos:lista')
        return render(request, self.template_name, {'form': form, 'formset': formset, 'object': pedido})


class PedidoDeleteView(LoginRequiredMixin, DeleteView):
    model = Pedido
    template_name = 'pedidos/pedido_confirm_delete.html'
    success_url = reverse_lazy('pedidos:lista')


class PedidoConfirmarPagoView(LoginRequiredMixin, View):
    def post(self, request, pk):
        pedido = get_object_or_404(Pedido, pk=pk)

        if pedido.estado == 'COMPLETADO':
            messages.warning(request, "Este pedido ya fue procesado como venta.")
            return redirect('pedidos:lista')

        detalles_pedido = pedido.detalles.all()
        if not detalles_pedido.exists():
            messages.error(request, "Este pedido no tiene productos.")
            return redirect('pedidos:lista')

        # Verificar stock antes de operar
        for d in detalles_pedido:
            stock = getattr(d.producto.inventario, 'stock_actual', 0)
            if d.cantidad > stock:
                messages.error(
                    request,
                    f"Stock insuficiente para '{d.producto.nombre}'. "
                    f"Disponible: {stock}, requerido: {d.cantidad}."
                )
                return redirect('pedidos:lista')

        with transaction.atomic():
            venta = Venta.objects.create(
                pedido=pedido,
                cliente=pedido.cliente,
                vendedor=request.user,
                metodo_pago='TRANSFERENCIA',
                total=0,
            )

            total = 0
            for d in detalles_pedido:
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=d.producto,
                    cantidad=d.cantidad,
                    precio_unitario=d.precio_unitario,
                )
                total += d.subtotal()

                # Descontar del inventario
                inventario = d.producto.inventario
                inventario.stock_actual -= d.cantidad
                inventario.save()

                # Auditoría/Kardex de movimiento
                MovimientoInventario.objects.create(
                    producto=d.producto,
                    tipo_movimiento='SALIDA',
                    cantidad=d.cantidad,
                    motivo=f"Venta #{venta.id} (Pedido #{pedido.id})",
                    usuario=request.user,
                )

            venta.total = total
            venta.save()

            pedido.estado = 'COMPLETADO'
            pedido.save()

        messages.success(request, f"Pedido #{pedido.id} confirmado. Venta #{venta.id} generada.")
        return redirect('pedidos:lista')
    
    