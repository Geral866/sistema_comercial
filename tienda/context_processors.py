from decouple import config


def carrito(request):
    carrito_sesion = request.session.get('carrito', {})
    cantidad_total = sum(carrito_sesion.values())
    return {
        'carrito_cantidad': cantidad_total,
        'whatsapp_numero': config('WHATSAPP_NUMERO'),
        'envio_gratis_desde': 100000,
    }
    