Sistema de Gestión Comercial y Tienda en Línea — Productos Naturales

Sistema web desarrollado en Django para la práctica profesional de Ingeniería de Software. Integra dos componentes conectados a una misma base de datos:

Tienda pública: catálogo de productos, carrito de compras y checkout con cierre de pedido vía WhatsApp.
Panel de gestión interna: administración de productos, categorías, inventario, clientes, pedidos, ventas y un dashboard de reportes.
Tecnologías utilizadas
Python 3 + Django
PostgreSQL
Bootstrap 5
python-decouple (variables de entorno)
Pillow (manejo de imágenes)
Estructura del proyecto
gestion_naturales/
├── config/         # Configuración del proyecto (settings, urls)
├── tienda/         # Vistas públicas: catálogo, carrito, checkout
├── productos/      # Productos y categorías
├── inventario/     # Stock y movimientos de inventario
├── clientes/       # Registro de clientes
├── pedidos/        # Pedidos generados desde la tienda pública
├── ventas/         # Ventas y detalle de venta
├── usuarios/       # Autenticación y roles internos
├── reportes/       # Dashboard
└── templates/      # Plantillas base (interna y pública)
Instalación y puesta en marcha
1. Clonar el repositorio
bash
git clone <url-del-repositorio>
cd gestion_naturales
2. Crear y activar el entorno virtual
bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
3. Instalar dependencias
bash
pip install django psycopg2-binary python-decouple pillow
4. Crear la base de datos en PostgreSQL

Desde pgAdmin o psql, crear una base de datos vacía (por ejemplo gestion_comercial). Django se encarga de crear las tablas mediante migraciones — no crear tablas manualmente.

5. Configurar variables de entorno

Crear un archivo .env en la raíz del proyecto (junto a manage.py) con el siguiente contenido:

DB_NAME=gestion_comercial
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432
WHATSAPP_NUMERO=573xxxxxxxxx

El .env no se sube al repositorio (está en .gitignore) porque contiene datos sensibles.

6. Aplicar migraciones
bash
python manage.py migrate
7. Crear un usuario administrador
bash
python manage.py createsuperuser
8. Ejecutar el servidor de desarrollo
bash
python manage.py runserver
Tienda pública: http://127.0.0.1:8000/
Panel de administración interno: http://127.0.0.1:8000/admin/
Módulos internos (productos, clientes, pedidos, ventas, inventario, reportes): accesibles desde el navbar tras iniciar sesión en /login/
Flujo general del sistema
Un cliente navega el catálogo público, agrega productos al carrito y completa el checkout con sus datos de envío.
Se genera un Pedido en estado "Pendiente" y el cliente es redirigido a WhatsApp con un mensaje ya armado para coordinar el pago y el despacho.
El negocio confirma el pago por WhatsApp y, desde el panel interno (/pedidos/), presiona "Confirmar pago".
El sistema genera automáticamente la Venta, descuenta el inventario y registra el movimiento en el historial de auditoría.
El Dashboard (/reportes/) muestra ventas del día/mes, productos más vendidos y alertas de stock bajo o agotado.
Reglas de negocio principales
El stock nunca puede quedar en negativo; toda venta valida disponibilidad antes de descontar.
Toda salida o entrada de inventario queda registrada en MovimientoInventario para trazabilidad.
Un cliente con ventas o pedidos asociados no puede eliminarse (protección de integridad referencial).
El precio de cada producto en una venta se toma siempre del precio actual en base de datos, nunca de lo que envíe el navegador.
Próximas fases (fuera del alcance de esta entrega)
Integración con una pasarela de pagos en línea (Wompi, PayU o Mercado Pago).
Autenticación de clientes en la tienda pública.
Aplicación móvil.
Facturación electrónica.
Autor

Yeraldin Arboleda Quintero — Práctica profesional en Ingeniería de Software.
