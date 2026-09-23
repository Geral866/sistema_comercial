from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('', views.VentaListView.as_view(), name='lista'),
    path('nueva/', views.VentaCreateView.as_view(), name='crear'),
    path('<int:pk>/eliminar/', views.VentaDeleteView.as_view(), name='eliminar'),
]
