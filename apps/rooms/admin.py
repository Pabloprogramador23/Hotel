from django.contrib import admin
from .models import Room, MaintenanceRecord

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('number', 'room_type', 'status', 'created_at', 'updated_at')
    list_filter = ('room_type', 'status')
    search_fields = ('number', 'description')
    ordering = ('number',)

@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('room', 'date', 'description')
    list_filter = ('date', 'room')
    search_fields = ('description',)
    ordering = ('-date',)
