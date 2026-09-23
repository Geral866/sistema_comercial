from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'documento', 'fecha_registro')
    search_fields = ('nombre', 'telefono', 'documento')
    