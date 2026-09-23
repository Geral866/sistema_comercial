from django.contrib import admin
from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'fecha_creacion')
    search_fields = ('nombre',)
    list_filter = ('activo',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'activo', 'fecha_actualizacion')
    search_fields = ('nombre', 'categoria__nombre')
    list_filter = ('categoria', 'activo')
    list_editable = ('precio', 'activo')
    
