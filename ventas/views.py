from django.db import transaction
from django.forms import inlineformset_factory
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DeleteView
from django.urls import reverse_lazy

from .models import Venta, DetalleVenta
from .forms import VentaForm, DetalleVentaForm
from productos.models import Producto
from inventario.models import MovimientoInventario

DetalleVentaFormSet = inlineformset_factory(
    Venta, DetalleVenta,
    form=DetalleVentaForm,
    extra=1, can_delete=True
)


class VentaListView(LoginRequiredMixin, ListView):
    model = Venta
    template_name = 'ventas/venta_list.html'
    context_object_name = 'ventas'
    paginate_by = 10

    def get_queryset(self):
        return Venta.objects.select_related('cliente', 'vendedor').order_by('-fecha_venta')


class VentaCreateView(LoginRequiredMixin, View):
    template_name = 'ventas/venta_form.html'

    def get(self, request):
        form = VentaForm()
        formset = DetalleVentaFormSet()
        
        productos_precios = {
            str(p.id): float(p.precio) 
            for p in Producto.objects.filter(activo=True)
        }
        
        return render(request, self.template_name, {
            'form': form, 
            'formset': formset, 
            'productos_precios': productos_precios
        })

    def post(self, request):
        form = VentaForm(request.POST)
        formset = DetalleVentaFormSet(request.POST)
        
        productos_precios = {
            str(p.id): float(p.precio) 
            for p in Producto.objects.filter(activo=True)
        }

        if form.is_valid() and formset.is_valid():
            detalles_validos = [
                f for f in formset 
                if f.cleaned_data and not f.cleaned_data.get('DELETE') and f.cleaned_data.get('producto')
            ]

            if not detalles_validos:
                messages.error(request, "La venta debe tener al menos un producto.")
                return render(request, self.template_name, {
                    'form': form, 
                    'formset': formset, 
                    'productos_precios': productos_precios
                })

            with transaction.atomic():
                # Crear la Venta (el total se calcula después, con los detalles ya guardados)
                venta = form.save(commit=False)
                venta.vendedor = request.user
                venta.total = 0
                venta.save()

                # Guardar detalles asociados (cada detalle.save() asigna su precio real)
                formset.instance = venta
                detalles = formset.save()

                # Calcular total real y actualizar stock e historial de inventario
                total = 0
                for detalle in detalles:
                    producto = detalle.producto
                    cantidad = detalle.cantidad
                    total += producto.precio * cantidad

                    # Restar stock en la app inventario
                    inventario = producto.inventario
                    inventario.stock_actual -= cantidad
                    inventario.save()

                    # Auditoría de movimiento tipo SALIDA
                    MovimientoInventario.objects.create(
                        producto=producto,
                        tipo_movimiento='SALIDA',
                        cantidad=cantidad,
                        motivo=f"Venta #{venta.id}",
                        usuario=request.user
                    )

                venta.total = total
                venta.save()

            messages.success(request, f"Venta #{venta.id} registrada correctamente.")
            return redirect('ventas:lista')

        return render(request, self.template_name, {
            'form': form, 
            'formset': formset, 
            'productos_precios': productos_precios
        })


class VentaDeleteView(LoginRequiredMixin, DeleteView):
    model = Venta
    template_name = 'ventas/venta_confirm_delete.html'
    success_url = reverse_lazy('ventas:lista')
    
    