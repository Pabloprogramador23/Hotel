from django.contrib import admin
from .models import Reservation, ReservationGuest, Room

class ReservationGuestInline(admin.TabularInline):
    model = ReservationGuest
    extra = 1

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('room', 'data_entrada', 'data_saida', 'ativa')
    list_filter = ('ativa', 'data_entrada', 'data_saida')
    search_fields = ('room__numero',)
    inlines = [ReservationGuestInline]

@admin.register(ReservationGuest)
class ReservationGuestAdmin(admin.ModelAdmin):
    list_display = ('nome', 'reserva', 'valor_devido', 'pago', 'metodo_pagamento')
    list_filter = ('pago', 'metodo_pagamento')
    search_fields = ('nome', 'reserva__room__numero')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('numero', 'status')
    list_filter = ('status',)
    search_fields = ('numero',)
