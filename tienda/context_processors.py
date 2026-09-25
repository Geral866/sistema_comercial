from productos.models import Producto


def carrito(request):
    carrito_sesion = request.session.get('carrito', {})
    cantidad_total = sum(carrito_sesion.values())
    return {'carrito_cantidad': cantidad_total}
