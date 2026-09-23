from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import ProtectedError
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Cliente


class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'clientes/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 10

    def get_queryset(self):
        return Cliente.objects.order_by('nombre')


class ClienteCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Cliente
    fields = ['nombre', 'documento', 'telefono', 'email', 'direccion']
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:lista')
    success_message = "Cliente registrado correctamente."


class ClienteUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Cliente
    fields = ['nombre', 'documento', 'telefono', 'email', 'direccion']
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:lista')
    success_message = "Cliente actualizado correctamente."


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'clientes/cliente_confirm_delete.html'
    success_url = reverse_lazy('clientes:lista')

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                f"No se puede eliminar a '{self.object.nombre}' porque tiene "
                f"pedidos o ventas registradas asociadas."
            )
            return redirect('clientes:lista')
        