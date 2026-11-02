from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('exportar/ventas/', views.ExportarVentasView.as_view(), name='exportar_ventas'),
]

