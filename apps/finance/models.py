from django.db import models

class Invoice(models.Model):
    reservation = models.ForeignKey('reservations.Reservation', on_delete=models.CASCADE, related_name='invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issued_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Invoice {self.id} - Reservation {self.reservation.id}"

class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Pagamento de R$ {self.amount:.2f} para Fatura {self.invoice.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Atualiza status da fatura após pagamento
        total_paid = sum(p.amount for p in self.invoice.payments.all())
        if total_paid >= self.invoice.amount:
            self.invoice.paid = True
            self.invoice.save()
        else:
            self.invoice.paid = False
            self.invoice.save()
