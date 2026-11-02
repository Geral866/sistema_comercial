import re
import urllib.parse

from decouple import config
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from clientes.models import Cliente
from pedidos.models import Pedido, DetallePedido
from productos.models import Producto, Categoria

MAX_POR_PRODUCTO = 20


# ---------- Utilidades ----------

def _es_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _stock(producto):
    inv = getattr(producto, 'inventario', None)
    return inv.stock_actual if inv else 0


def _normalizar_telefono(valor):
    digitos = re.sub(r'\D', '', valor or '')
    if digitos.startswith('57') and len(digitos) == 12:
        digitos = digitos[2:]
    return digitos


def _normalizar_documento(valor):
    return re.sub(r'[\s.]', '', valor or '')


def _serializar_productos(qs):
    return [{
        'id': p.id,
        'nombre': p.nombre,
        'categoria': p.categoria.nombre,
        'categoria_id': p.categoria_id,
        'precio': float(p.precio),
        'imagen': p.imagen.url if p.imagen else '',
        'descripcion': p.descripcion or '',
        'stock': _stock(p),
    } for p in qs]


def _resumen_carrito(request):
    carrito = request.session.get('carrito', {})
    ids = [int(k) for k in carrito if str(k).isdigit()]
    productos = {
        p.id: p for p in
        Producto.objects.filter(pk__in=ids, activo=True).select_related('inventario')
    }
    items, total = [], 0
    for clave, cantidad in carrito.items():
        producto = productos.get(int(clave)) if str(clave).isdigit() else None
        if not producto:
            continue
        subtotal = producto.precio * cantidad
        total += subtotal
        items.append({
            'id': producto.id, 'nombre': producto.nombre, 'cantidad': cantidad,
            'precio': float(producto.precio), 'subtotal': float(subtotal),
            'imagen': producto.imagen.url if producto.imagen else '',
            'stock': _stock(producto),
        })
    return items, float(total)


def _respuesta_carrito(request, ok, mensaje, status=200, destino='tienda:catalogo'):
    if _es_ajax(request):
        items, total = _resumen_carrito(request)
        return JsonResponse({
            'ok': ok, 'mensaje': mensaje, 'items': items, 'total': total,
            'cantidad_total': sum(request.session.get('carrito', {}).values()),
        }, status=status)
    (messages.success if ok else messages.error)(request, mensaje)
    return redirect(destino)


# ---------- Catálogo ----------

def inicio(request):
    productos_destacados = (Producto.objects.filter(activo=True)
                            .select_related('categoria').order_by('-fecha_creacion')[:8])
    categorias = Categoria.objects.filter(activo=True)
    return render(request, 'tienda/inicio.html', {
        'productos_destacados': productos_destacados,
        'categorias': categorias,
    })


def catalogo(request):
    productos = (Producto.objects.filter(activo=True)
                 .select_related('categoria', 'inventario').order_by('nombre'))
    categorias = Categoria.objects.filter(activo=True)
    return render(request, 'tienda/catalogo.html', {
        'categorias': categorias,
        'productos_json': _serializar_productos(productos),
    })


def detalle_producto(request, pk):
    producto = get_object_or_404(
        Producto.objects.select_related('categoria', 'inventario'), pk=pk, activo=True)
    return render(request, 'tienda/detalle_producto.html', {
        'producto': producto, 'stock': _stock(producto)})


# ---------- Carrito ----------

def ver_carrito(request):
    items, total = _resumen_carrito(request)
    return render(request, 'tienda/carrito.html', {'items': items, 'total': total})


def carrito_json(request):
    items, total = _resumen_carrito(request)
    return JsonResponse({
        'items': items, 'total': total,
        'cantidad_total': sum(request.session.get('carrito', {}).values()),
    })


@require_POST
def agregar_carrito(request, pk):
    producto = get_object_or_404(
        Producto.objects.select_related('inventario'), pk=pk, activo=True)
    try:
        cantidad = int(request.POST.get('cantidad', 1))
    except (TypeError, ValueError):
        cantidad = 0
    if cantidad < 1:
        return _respuesta_carrito(request, False, 'La cantidad no es válida.', 400)

    stock = _stock(producto)
    if stock <= 0:
        return _respuesta_carrito(request, False, f"'{producto.nombre}' está agotado.", 400)

    carrito = request.session.get('carrito', {})
    clave = str(pk)
    limite = min(stock, MAX_POR_PRODUCTO)
    nueva = carrito.get(clave, 0) + cantidad
    if nueva > limite:
        return _respuesta_carrito(
            request, False,
            f"Solo puedes llevar {limite} unidad(es) de '{producto.nombre}'.", 400)

    carrito[clave] = nueva
    request.session['carrito'] = carrito
    return _respuesta_carrito(request, True, f"'{producto.nombre}' agregado al carrito.")


@require_POST
def actualizar_cantidad_carrito(request, pk):
    accion = request.POST.get('accion')
    carrito = request.session.get('carrito', {})
    clave = str(pk)
    mensaje = ''

    if clave in carrito:
        if accion == 'incrementar':
            producto = (Producto.objects.filter(pk=pk, activo=True)
                        .select_related('inventario').first())
            limite = min(_stock(producto), MAX_POR_PRODUCTO) if producto else 0
            if carrito[clave] + 1 <= limite:
                carrito[clave] += 1
            else:
                mensaje = 'No hay más unidades disponibles de este producto.'
        elif accion == 'decrementar':
            carrito[clave] -= 1
            if carrito[clave] <= 0:
                del carrito[clave]
        elif accion == 'eliminar':
            del carrito[clave]

    request.session['carrito'] = carrito
    items, total = _resumen_carrito(request)
    return JsonResponse({
        'items': items, 'total': total, 'mensaje': mensaje,
        'cantidad_total': sum(carrito.values()),
    })


@require_POST
def eliminar_del_carrito(request, pk):
    carrito = request.session.get('carrito', {})
    carrito.pop(str(pk), None)
    request.session['carrito'] = carrito
    return _respuesta_carrito(request, True, 'Producto eliminado del carrito.', destino='tienda:ver_carrito')


# ---------- Checkout ----------

def _validar_checkout(d):
    """Normaliza documento y teléfono dentro de `d` y devuelve la lista de errores."""
    errores = []
    d['documento'] = _normalizar_documento(d['documento'])
    d['telefono'] = _normalizar_telefono(d['telefono'])

    if len(d['nombre']) < 3 or len(d['nombre']) > 150:
        errores.append('Ingresa tu nombre completo.')
    if not re.fullmatch(r'\d{5,15}', d['documento']):
        errores.append('La cédula debe tener solo números (entre 5 y 15 dígitos).')
    if not re.fullmatch(r'3\d{9}', d['telefono']):
        errores.append('Ingresa un celular colombiano válido de 10 dígitos (ej: 3001234567).')
    if not 2 <= len(d['ciudad']) <= 100:
        errores.append('Ingresa tu ciudad.')
    if not 5 <= len(d['direccion']) <= 200:
        errores.append('Ingresa una dirección de entrega completa.')
    if len(d['notas']) > 500:
        errores.append('Las notas no pueden superar 500 caracteres.')
    return errores


def _obtener_o_crear_cliente(d):
    por_doc = Cliente.objects.filter(documento=d['documento']).first()
    por_tel = Cliente.objects.filter(telefono=d['telefono']).first()

    if por_doc and por_tel and por_doc.pk != por_tel.pk:
        raise ValidationError(
            'Ese celular y esa cédula ya están registrados con datos distintos. '
            'Verifica la información o escríbenos por WhatsApp.')
    if por_tel and por_tel.documento and por_tel.documento != d['documento']:
        raise ValidationError(
            'Ese celular ya está registrado con otra cédula. '
            'Verifica la información o escríbenos por WhatsApp.')

    cliente = por_doc or por_tel
    if cliente is None:
        cliente = Cliente()
    cliente.nombre = d['nombre']
    cliente.documento = d['documento']
    cliente.telefono = d['telefono']
    cliente.ciudad = d['ciudad']
    cliente.direccion = d['direccion']
    cliente.save()
    return cliente


def checkout(request):
    items, total = _resumen_carrito(request)
    if not items:
        messages.error(request, 'Tu carrito está vacío.')
        return redirect('tienda:catalogo')

    datos, errores = {}, []

    if request.method == 'POST':
        campos = ('nombre', 'documento', 'telefono', 'ciudad', 'direccion', 'notas')
        datos = {c: request.POST.get(c, '').strip() for c in campos}
        errores = _validar_checkout(datos)

        for it in items:
            if it['cantidad'] > it['stock']:
                errores.append(f"'{it['nombre']}': solo quedan {it['stock']} unidad(es) disponibles.")

        if not errores:
            productos = Producto.objects.in_bulk([it['id'] for it in items])
            try:
                with transaction.atomic():
                    cliente = _obtener_o_crear_cliente(datos)
                    pedido = Pedido.objects.create(
                        cliente=cliente, estado='PENDIENTE',
                        observaciones=datos['notas'],
                        ciudad_envio=datos['ciudad'],
                        direccion_envio=datos['direccion'],
                    )
                    DetallePedido.objects.bulk_create([
                        DetallePedido(
                            pedido=pedido, producto=productos[it['id']],
                            cantidad=it['cantidad'],
                            precio_unitario=productos[it['id']].precio,
                        ) for it in items
                    ])
            except ValidationError as e:
                errores.extend(e.messages)
            else:
                request.session['carrito'] = {}
                request.session['ultimo_pedido_id'] = pedido.id
                return redirect('tienda:pedido_confirmado', pedido_id=pedido.id)

    return render(request, 'tienda/checkout.html', {
        'items': items, 'total': total, 'datos': datos, 'errores': errores})


def pedido_confirmado(request, pedido_id):
    # Solo se puede ver el pedido que esta misma sesión acaba de crear
    if request.session.get('ultimo_pedido_id') != pedido_id:
        raise Http404
    pedido = get_object_or_404(Pedido.objects.select_related('cliente'), pk=pedido_id)

    ciudad = pedido.ciudad_envio or pedido.cliente.ciudad or ''
    direccion = pedido.direccion_envio or pedido.cliente.direccion or ''

    lineas = [f"Hola, quiero confirmar mi pedido #{pedido.id}:"]
    for detalle in pedido.detalles.select_related('producto'):
        lineas.append(f"- {detalle.cantidad} x {detalle.producto.nombre} (${detalle.subtotal()})")
    lineas.append(f"Total: ${pedido.total}")
    lineas.append(f"Nombre: {pedido.cliente.nombre}")
    lineas.append(f"Ciudad: {ciudad}")
    lineas.append(f"Dirección: {direccion}")
    if pedido.observaciones:
        lineas.append(f"Notas: {pedido.observaciones}")

    numero_whatsapp = config('WHATSAPP_NUMERO')
    link_whatsapp = f"https://wa.me/{numero_whatsapp}?text={urllib.parse.quote(chr(10).join(lineas))}"
    return render(request, 'tienda/pedido_confirmado.html', {
        'pedido': pedido, 'link_whatsapp': link_whatsapp})


def consultar_pedido(request):
    pedidos = None
    telefono = request.GET.get('telefono', '').strip()
    documento = _normalizar_documento(request.GET.get('documento', ''))
    if telefono and documento:
        pedidos = (Pedido.objects
                   .filter(cliente__telefono=_normalizar_telefono(telefono),
                           cliente__documento=documento)
                   .select_related('cliente').prefetch_related('detalles__producto')
                   .order_by('-fecha_pedido')[:20])
    return render(request, 'tienda/consultar_pedido.html', {
        'pedidos': pedidos, 'telefono': telefono, 'documento': documento})
    
    