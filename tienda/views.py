import urllib.parse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from decouple import config

from productos.models import Producto, Categoria
from clientes.models import Cliente
from pedidos.models import Pedido, DetallePedido


def inicio(request):
    productos_destacados = Producto.objects.filter(activo=True)[:6]
    categorias = Categoria.objects.filter(activo=True)
    return render(request, 'tienda/inicio.html', {
        'productos_destacados': productos_destacados,
        'categorias': categorias,
    })


def catalogo(request):
    productos = Producto.objects.filter(activo=True).select_related('categoria')
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    categorias = Categoria.objects.filter(activo=True)
    return render(request, 'tienda/catalogo.html', {
        'productos': productos,
        'categorias': categorias,
        'categoria_activa': int(categoria_id) if categoria_id else None,
    })


def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    return render(request, 'tienda/detalle_producto.html', {'producto': producto})


def agregar_carrito(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    cantidad = int(request.POST.get('cantidad', 1))

    carrito = request.session.get('carrito', {})
    clave = str(pk)
    carrito[clave] = carrito.get(clave, 0) + cantidad
    request.session['carrito'] = carrito

    messages.success(request, f"'{producto.nombre}' agregado al carrito.")
    return redirect('tienda:catalogo')


def ver_carrito(request):
    carrito = request.session.get('carrito', {})
    items = []
    total = 0
    for producto_id, cantidad in carrito.items():
        try:
            producto = Producto.objects.get(pk=producto_id, activo=True)
        except Producto.DoesNotExist:
            continue
        subtotal = producto.precio * cantidad
        total += subtotal
        items.append({'producto': producto, 'cantidad': cantidad, 'subtotal': subtotal})

    return render(request, 'tienda/carrito.html', {'items': items, 'total': total})


def eliminar_del_carrito(request, pk):
    carrito = request.session.get('carrito', {})
    carrito.pop(str(pk), None)
    request.session['carrito'] = carrito
    messages.success(request, "Producto eliminado del carrito.")
    return redirect('tienda:ver_carrito')


def checkout(request):
    carrito = request.session.get('carrito', {})
    if not carrito:
        messages.error(request, "Tu carrito está vacío.")
        return redirect('tienda:catalogo')

    items = []
    total = 0
    for producto_id, cantidad in carrito.items():
        try:
            producto = Producto.objects.get(pk=producto_id, activo=True)
        except Producto.DoesNotExist:
            continue
        subtotal = producto.precio * cantidad
        total += subtotal
        items.append({'producto': producto, 'cantidad': cantidad, 'subtotal': subtotal})

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        documento = request.POST.get('documento', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        ciudad = request.POST.get('ciudad', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        notas = request.POST.get('notas', '').strip()

        if not (nombre and documento and telefono and ciudad and direccion):
            messages.error(request, "Por favor completa todos los campos obligatorios.")
            return render(request, 'tienda/checkout.html', {'items': items, 'total': total})

        with transaction.atomic():
            cliente, _ = Cliente.objects.get_or_create(
                telefono=telefono,
                defaults={
                    'nombre': nombre, 'documento': documento,
                    'ciudad': ciudad, 'direccion': direccion,
                }
            )
            pedido = Pedido.objects.create(
                cliente=cliente, estado='PENDIENTE', observaciones=notas
            )
            for item in items:
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=item['producto'],
                    cantidad=item['cantidad'],
                    precio_unitario=item['producto'].precio,
                )

        request.session['carrito'] = {}
        return redirect('tienda:pedido_confirmado', pedido_id=pedido.id)

    return render(request, 'tienda/checkout.html', {'items': items, 'total': total})


def pedido_confirmado(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)

    lineas = [f"Hola, quiero confirmar mi pedido #{pedido.id}:"]
    for detalle in pedido.detalles.all():
        lineas.append(f"- {detalle.cantidad} x {detalle.producto.nombre} (${detalle.subtotal()})")
    lineas.append(f"Total: ${pedido.total}")
    lineas.append(f"Nombre: {pedido.cliente.nombre}")
    lineas.append(f"Ciudad: {pedido.cliente.ciudad}")
    lineas.append(f"Dirección: {pedido.cliente.direccion}")
    if pedido.observaciones:
        lineas.append(f"Notas: {pedido.observaciones}")
    mensaje = "\n".join(lineas)

    numero_whatsapp = config('WHATSAPP_NUMERO')
    link_whatsapp = f"https://wa.me/{numero_whatsapp}?text={urllib.parse.quote(mensaje)}"

    return render(request, 'tienda/pedido_confirmado.html', {
        'pedido': pedido, 'link_whatsapp': link_whatsapp
    })
    