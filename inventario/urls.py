from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    path('', views.InventarioListView.as_view(), name='lista'),
    path('movimientos/', views.MovimientoListView.as_view(), name='movimientos'),
    path('movimientos/nuevo/', views.MovimientoCreateView.as_view(), name='crear_movimiento'),
]
