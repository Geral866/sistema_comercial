from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('productos/', include('productos.urls')),
    path('clientes/', include('clientes.urls')),
    path('pedidos/', include('pedidos.urls')),
    path('ventas/', include('ventas.urls')),
    path('', RedirectView.as_view(pattern_name='productos:lista'), name='home'),
    path('inventario/', include('inventario.urls')),
    path('reportes/', include('reportes.urls')),
    path('', RedirectView.as_view(pattern_name='reportes:dashboard'), name='home'),
    # más adelante: clientes, pedidos, ventas, reportes
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    