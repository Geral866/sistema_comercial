from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView
from .models import Inventario, MovimientoInventario


class InventarioListView(LoginRequiredMixin, ListView):
    model = Inventario
    template_name = 'inventario/inventario_list.html'
    context_object_name = 'inventarios'
    paginate_by = 15

    def get_queryset(self):
        return Inventario.objects.select_related('producto').order_by('producto__nombre')


class MovimientoListView(LoginRequiredMixin, ListView):
    model = MovimientoInventario
    template_name = 'inventario/movimiento_list.html'
    context_object_name = 'movimientos'
    paginate_by = 20

    def get_queryset(self):
        return MovimientoInventario.objects.select_related('producto', 'usuario').order_by('-fecha')


class MovimientoCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = MovimientoInventario
    fields = ['producto', 'tipo_movimiento', 'cantidad', 'motivo']
    template_name = 'inventario/movimiento_form.html'
    success_url = reverse_lazy('inventario:movimientos')
    success_message = "Movimiento registrado correctamente."

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)
    