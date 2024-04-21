# tasks.py

from pm1.celery import shared_task
from django.utils import timezone
from .models import InventoryItem, Notification

@shared_task
def check_medicine_expiration():
    expired_medicines, expiring_soon_medicines = InventoryItem.get_expired_and_expiring_soon()

    for medicine in expired_medicines:
        message = f"{medicine.medicine_name} has expired on {medicine.expiry_date}."
        create_notification(message)

    for medicine in expiring_soon_medicines:
        message = f"{medicine.medicine_name} will expire on {medicine.expiry_date}."
        create_notification(message)

def create_notification(message):
    Notification.objects.create(message=message)
