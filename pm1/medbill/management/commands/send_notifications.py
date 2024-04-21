# myapp/management/commands/send_notifications.py

from django.core.management.base import BaseCommand
from medbill.models import InventoryItem, Notification
from datetime import date, timedelta
from django_cron import CronJobBase, Schedule

class SendNotifications(CronJobBase):
    RUN_EVERY_MINS = 24 * 60  # Run every 24 hours

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'medbil.send_notifications'  # a unique code

    def do(self):
        # Get medicines that are expired or expiring within 6 months
        today = date.today()
        six_months_later = today + timedelta(days=180)

        expired_medicines = InventoryItem.objects.filter(expiry_date__lt=today)
        expiring_medicines = InventoryItem.objects.filter(expiry_date__lte=six_months_later, expiry_date__gt=today)

        # Send notifications for expired medicines
        for medicine in expired_medicines:
            notification_message = f"Medicine {medicine.medicine_name} has expired!"
            create_notification(notification_message, medicine)

        # Send notifications for expiring medicines
        for medicine in expiring_medicines:
            notification_message = f"Medicine {medicine.medicine_name} will expire soon on {medicine.expiry_date}"
            create_notification(notification_message, medicine)

    def create_notification(self, message, medicine):
        Notification.objects.create(message=message, medicine=medicine)
