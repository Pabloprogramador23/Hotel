from django.db import models
from django.utils import timezone


class Room(models.Model):
    class Status(models.TextChoices):
        DISPONIVEL = 'disponivel', 'Disponivel'
        OCUPADO = 'ocupado', 'Ocupado'

    numero = models.CharField(max_length=10, unique=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DISPONIVEL,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['numero']

    def __str__(self) -> str:
        return f"Quarto {self.numero}"

    def ocupar(self):
        self.status = Room.Status.OCUPADO
        self.save(update_fields=['status', 'atualizado_em'])

    def liberar(self):
        self.status = Room.Status.DISPONIVEL
        self.save(update_fields=['status', 'atualizado_em'])


class ReservationQuerySet(models.QuerySet):
    def ativas(self):
        return self.filter(ativa=True, data_saida__isnull=True)


class Reservation(models.Model):
    room = models.ForeignKey(Room, related_name='reservas', on_delete=models.CASCADE)
    data_entrada = models.DateTimeField(auto_now_add=True)
    data_saida = models.DateTimeField(blank=True, null=True)
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    objects = ReservationQuerySet.as_manager()

    class Meta:
        ordering = ['-data_entrada']

    def __str__(self) -> str:
        return f"Reserva #{self.pk} - Quarto {self.room.numero}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.ocupando:
            self.room.ocupar()

    def encerrar(self, quando=None):
        quando = quando or timezone.now()
        self.data_saida = quando
        self.ativa = False
        self.save(update_fields=['data_saida', 'ativa', 'atualizado_em'])
        self.room.liberar()

    @property
    def ocupando(self) -> bool:
        return self.ativa and self.data_saida is None


class ReservationGuest(models.Model):
    class MetodoPagamento(models.TextChoices):
        PIX = 'PIX', 'Pix'
        DINHEIRO = 'DINHEIRO', 'Dinheiro'
        PENDENTE = 'PENDENTE', 'Pendente'

    reserva = models.ForeignKey(Reservation, related_name='hospedes', on_delete=models.CASCADE)
    nome = models.CharField(max_length=255)
    valor_devido = models.DecimalField(max_digits=10, decimal_places=2)
    pago = models.BooleanField(default=False)
    metodo_pagamento = models.CharField(
        max_length=20,
        choices=MetodoPagamento.choices,
        default=MetodoPagamento.PENDENTE,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self) -> str:
        return f"{self.nome} - Reserva {self.reserva_id}"

    def registrar_pagamento(self, metodo: str):
        self.metodo_pagamento = metodo
        self.pago = metodo != ReservationGuest.MetodoPagamento.PENDENTE
        self.save(update_fields=['metodo_pagamento', 'pago', 'atualizado_em'])
