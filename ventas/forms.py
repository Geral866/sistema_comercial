from django import forms
from .models import Venta, DetalleVenta


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['pedido', 'cliente', 'metodo_pago']


class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model = DetalleVenta
        fields = ['producto', 'cantidad']   # <-- precio_unitario YA NO está aquí

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['cantidad'].initial = 1

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')

        if producto and cantidad:
            stock_disponible = getattr(producto.inventario, 'stock_actual', 0)
            if cantidad > stock_disponible:
                raise forms.ValidationError(
                    f"Stock insuficiente para '{producto.nombre}'. "
                    f"Disponible: {stock_disponible}, solicitado: {cantidad}."
                )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.producto_id:
            instance.precio_unitario = instance.producto.precio
        if commit:
            instance.save()
        return instance
    