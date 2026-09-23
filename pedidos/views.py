from django.forms import inlineformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DeleteView
from django.urls import reverse_lazy
from .models import Pedido, DetallePedido
from .forms import PedidoForm

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
    