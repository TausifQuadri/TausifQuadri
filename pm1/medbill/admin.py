# admin.py

from django.contrib import admin
from .models import InventoryItem, Patient, Billing, BillingItem

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['medicine_name', 'quantity', 'manufacturer', 'date_of_manufacture', 'expiry_date', 'price', 'category']
    search_fields = ['medicine_name', 'manufacturer']

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['name', 'date_prescribed', 'prescribing_doctor','symptoms']
    search_fields = ['name', 'prescribing_doctor']

@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ['invoice_number','patient', 'total_amount', 'discount', 'profit' ]
    search_fields = ['patient__name','invoice_number']

@admin.register(BillingItem)
class BillingItemAdmin(admin.ModelAdmin):
    list_display = ['invoice_number','billing', 'medicine', 'quantity', 'total_price', 'profit']
    search_fields = ['billing__patient__name', 'medicine__medicine_name']
