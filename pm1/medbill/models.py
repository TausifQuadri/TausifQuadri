from django.db import models
from datetime import date, timedelta

class InventoryItem(models.Model):
    medicine_name = models.CharField(max_length=100, unique=True)
    quantity = models.IntegerField()
    manufacturer = models.CharField(max_length=100)
    date_of_manufacture = models.DateField(default=date.today)
    expiry_date = models.DateField(default=date.today() + timedelta(days=180))
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    batch_number = models.CharField(max_length=50, default='DEFAULT_BATCH')

    CATEGORY_CHOICES = [
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('vial', 'Vial'),
        ('syrup', 'Syrup'),
        ('injection', 'Injection'),
        ('ointment', 'Ointment'),
        ('drop', 'Drop'),
        ('powder', 'Powder'),
        ('cream', 'Cream'),
        ('gel', 'Gel'),
        ('liquid', 'Liquid'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
def is_expired(self):
    return self.expiry_date < timezone.now().date()

def is_expiring_soon(self):
    six_months_later = timezone.now().date() + timezone.timedelta(days=180)
    return timezone.now().date() < self.expiry_date <= six_months_later
@classmethod
def get_expired_and_expiring_soon(cls):
    expired_medicines = cls.objects.filter(expiry_date__lt=timezone.now().date())
    expiring_soon_medicines = cls.objects.filter(
        expiry_date__gt=timezone.now().date(),
        expiry_date__lte=timezone.now().date() + timezone.timedelta(days=180),
    )
    return expired_medicines, expiring_soon_medicines

def __str__(self):
    return self.medicine_name

class Patient(models.Model):
    name = models.CharField(max_length=100)
    date_prescribed = models.DateField()
    prescribing_doctor = models.CharField(max_length=100)
    additional_notes = models.TextField(blank=True, null=True)
    symptoms=models.TextField(blank=True, null=True)
    
    
    

    def __str__(self):
        return self.name

class Billing(models.Model):
    invoice_number = models.CharField(max_length=20, unique=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount=models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calculate_total_amount(self):
        total_amount = sum(item.total_price for item in self.billingitem_set.all())
        self.net_amount=total_amount
        total_amount -= (total_amount * (self.discount / 100))  # Subtracting discount
        return total_amount

    def calculate_profit(self):
        profit = sum(item.calculate_profit() for item in self.billingitem_set.all())
        return profit -(self.net_amount * (self.discount / 100))

    def save(self, *args, **kwargs):
        try:
            if not self.id:
                super(Billing, self).save(*args, **kwargs)
            else:
                super(Billing, self).save(*args, **kwargs)

            # Update total_amount and profit after saving
            self.total_amount = self.calculate_total_amount()
            self.profit = self.calculate_profit()

            super(Billing, self).save(*args, **kwargs)

        except Exception as e:
            print(f"An error occurred while saving Billing instance: {str(e)}")

    def __str__(self):
        return f'Billing for {self.patient.name}'

class BillingItem(models.Model):
    billing = models.ForeignKey(Billing, on_delete=models.CASCADE)
    medicine = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    invoice_number = models.CharField(max_length=20,  blank=True)

    def calculate_profit(self):
        cost_price = self.medicine.cost_price
        selling_price = self.medicine.price  # Update: Use the price from InventoryItem
        profit_per_item = (selling_price - cost_price) * self.quantity
        return profit_per_item

    def save(self, *args, **kwargs):
        if self.quantity <= self.medicine.quantity:
            self.medicine.quantity -= self.quantity
            self.medicine.save()

            self.total_price = self.medicine.price * self.quantity  # Update: Use the price from InventoryItem
            self.profit = self.calculate_profit()
            super().save(*args, **kwargs)
        else:
            # Handle insufficient quantity in inventory
            raise ValueError(f" {self.medicine.medicine_name} Insufficient quantity in inventory (out of stock)")

    def __str__(self):
        return f'{self.quantity} units of {self.medicine.medicine_name} in {self.billing}'
class Notification(models.Model):
    medicine = models.ForeignKey(InventoryItem, on_delete=models.CASCADE,default=None)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    cleared = models.BooleanField(default=False)
    @classmethod
    def create_notification(cls, message, medicine=None):
        # Check if a similar uncleared notification already exists
        similar_notification = cls.objects.filter(message=message, cleared=False).first()

        if not similar_notification:
            # If no similar uncleared notification exists, create a new one
            notification = cls(message=message, medicine=medicine)
            notification.save()

    def __str__(self):
        return f"{self.message} - {'Cleared' if self.cleared else 'Uncleared'}"

    def is_expired(self):
        return timezone.now() - self.created_at > timezone.timedelta(hours=24)
#class date(models.Model):
    #created_at = models.DateTimeField(auto_now_add=True)
    




