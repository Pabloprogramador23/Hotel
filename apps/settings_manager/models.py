from django.db import models

class SystemSetting(models.Model):
    """
    Modelo para armazenar configurações do sistema em formato chave-valor.
    Migrado do app administration para settings_manager.
    """
    key = models.CharField(max_length=255, unique=True, verbose_name="Chave")
    value = models.TextField(verbose_name="Valor")
    description = models.CharField(max_length=255, blank=True, verbose_name="Descrição")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Configuração do Sistema"
        verbose_name_plural = "Configurações do Sistema"
        ordering = ["key"]

    def __str__(self):
        return f"{self.key}: {self.value}"
