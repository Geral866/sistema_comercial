from django.db import models


class Cliente(models.Model):
    nombre = models.CharField(max_length=150, verbose_name="Nombre o Razón Social")
    documento = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="NIT / Cédula")
    telefono = models.CharField(max_length=20, unique=True, verbose_name="Teléfono / WhatsApp")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo electrónico")
    direccion = models.TextField(blank=True, null=True, verbose_name="Dirección de envío")
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")
    ciudad = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ciudad")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.documento})"