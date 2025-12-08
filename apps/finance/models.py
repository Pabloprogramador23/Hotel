from django.db import models


class LedgerAdjustment(models.Model):
    class Tipo(models.TextChoices):
        CREDITO = 'credito', 'Crédito'
        DEBITO = 'debito', 'Débito'

    reservation = models.ForeignKey(
        'reservations.Reservation',
        on_delete=models.CASCADE,
        related_name='ajustes_financeiros',
        null=True,
        blank=True,
    )
    descricao = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=30, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        destino = f"Reserva {self.reservation_id}" if self.reservation_id else 'Operação Geral'
        return f"{self.get_tipo_display()} - {destino} - R$ {self.valor}"

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('utilities', 'Contas de Serviços (Água/Luz/Internet)'),
        ('supplies', 'Suprimentos'),
        ('maintenance', 'Manutenção'),
        ('staff', 'Salários e Benefícios'),
        ('marketing', 'Marketing e Publicidade'),
        ('taxes', 'Impostos e Taxas'),
        ('other', 'Outros'),
    ]
    
    description = models.CharField(max_length=255, verbose_name="Descrição")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other', verbose_name="Categoria")
    date_created = models.DateField(auto_now_add=True, verbose_name="Data de Registro")
    payment_date = models.DateField(verbose_name="Data de Pagamento")
    payment_method = models.CharField(max_length=50, verbose_name="Método de Pagamento")
    receipt = models.FileField(upload_to='expenses/receipts/', blank=True, null=True, verbose_name="Comprovante")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"
    
    def __str__(self):
        return f"{self.description} - R$ {self.amount} ({self.get_category_display()})"

class ExtraIncome(models.Model):
    description = models.CharField(max_length=255, verbose_name="Descrição")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    date_created = models.DateField(auto_now_add=True, verbose_name="Data de Registro")
    received_date = models.DateField(verbose_name="Data de Recebimento")
    method = models.CharField(max_length=50, verbose_name="Método de Recebimento")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Receita Avulsa"
        verbose_name_plural = "Receitas Avulsas"

    def __str__(self):
        return f"{self.description} - R$ {self.amount}"
