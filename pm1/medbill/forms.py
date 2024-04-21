from django import forms
from .models import InventoryItem

class InventoryRegistrationForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['medicine_name', 'quantity', 'manufacturer', 'date_of_manufacture', 'expiry_date', 'price','cost_price', 'description', 'batch_number', 'category']
        widgets = {
            'date_of_manufacture': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

class BillingForm(forms.Form):
    patient_name = forms.CharField(label='Patient Name', max_length=100)
    medicines_and_quantities = forms.CharField(label='Medicines and Quantities', widget=forms.Textarea(attrs={'rows': 2}))
    date_prescribed = forms.DateField(label='Date Prescribed', widget=forms.DateInput(attrs={'type': 'date'}))
    prescribing_doctor = forms.CharField(label='Prescribing Doctor', max_length=100)
    additional_notes = forms.CharField(label='Additional Notes', widget=forms.Textarea, required=False)
    discount = forms.DecimalField(label='Discount', required=False, initial=0, max_digits=5, decimal_places=2)

    def clean_medicines_and_quantities(self):
        data = self.cleaned_data['medicines_and_quantities']
        pairs = data.split('\n')

        cleaned_data = []
        for pair in pairs:
            pair = pair.strip()
            if not pair:
                continue
            parts = pair.split(',')
            if len(parts) != 2:
                raise forms.ValidationError("Invalid input format. Please provide medicine and quantity separated by a comma.")
            medicine_name, quantity = parts
            medicine_name = medicine_name.strip()
            quantity = quantity.strip()
            if not medicine_name or not quantity.isdigit() or int(quantity) < 1:
                raise forms.ValidationError("Invalid medicine or quantity. Please check your input.")
            cleaned_data.append((medicine_name, int(quantity)))

        return cleaned_data

    def clean_discount(self):
        discount = self.cleaned_data['discount']
        if discount < 0:
            raise forms.ValidationError("Discount cannot be negative.")
        return discount

    def calculate_total_price(self):
        total_price = sum(quantity * self.calculate_individual_price(medicine_name, quantity)
                         for medicine_name, quantity in self.cleaned_data['medicines_and_quantities'])
        discount = self.cleaned_data['discount']
        discounted_amount = (discount / 100) * total_price
        return total_price - discounted_amount

    def calculate_individual_price(self, medicine_name, quantity):
        try:
            medicines = InventoryItem.objects.filter(medicine_name=medicine_name)

            if medicines.exists():
                medicine = medicines.first()
                return medicine.price * quantity
            else:
                return 0
        except InventoryItem.DoesNotExist:
            return 0
class UpdateInventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['medicine_name', 'quantity', 'manufacturer', 'date_of_manufacture', 'expiry_date', 'price', 'cost_price', 'description', 'batch_number', 'category']
        widgets = {
            'date_of_manufacture': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        def clean(self):
        # Remove read-only attribute on form validation, allowing user input
            for field_name in self.fields:
                self.fields[field_name].widget.attrs.pop('readonly', None)

            return super().clean()