from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Producto
from .models import Categoria  # agrega Categoria al import existente de Producto

class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = 'productos/categoria_list.html'
    context_object_name = 'categorias'

    def get_queryset(self):
        return Categoria.objects.order_by('nombre')


class CategoriaCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Categoria
    fields = ['nombre', 'descripcion', 'activo']
    template_name = 'productos/categoria_form.html'
    success_url = reverse_lazy('productos:categorias')
    success_message = "Categoría creada correctamente."

class ProductoListView(LoginRequiredMixin, ListView):
    model = Producto
    template_name = 'productos/producto_list.html'
    context_object_name = 'productos'
    paginate_by = 10

    def get_queryset(self):
        return Producto.objects.select_related('categoria').order_by('nombre')


class ProductoCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Producto
    fields = ['categoria', 'nombre', 'descripcion', 'precio', 'imagen', 'stock_minimo', 'activo']
    template_name = 'productos/producto_form.html'
    success_url = reverse_lazy('productos:lista')
    success_message = "Producto creado correctamente."


class ProductoUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Producto
    fields = ['categoria', 'nombre', 'descripcion', 'precio', 'imagen', 'stock_minimo', 'activo']
    template_name = 'productos/producto_form.html'
    success_url = reverse_lazy('productos:lista')
    success_message = "Producto actualizado correctamente."


class ProductoDeleteView(LoginRequiredMixin, DeleteView):
    model = Producto
    template_name = 'productos/producto_confirm_delete.html'
    success_url = reverse_lazy('productos:lista')
    