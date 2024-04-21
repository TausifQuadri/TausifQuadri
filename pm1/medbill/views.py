from django.shortcuts import render, HttpResponse, redirect, get_object_or_404

from medbill.admin import InventoryItemAdmin
from .models import Billing, BillingItem, InventoryItem, Patient

from django.utils import timezone
from .models import Notification,date
from .forms import BillingForm
from django.template.loader import get_template
from django.views import View
from reportlab.pdfgen import canvas
from io import BytesIO
from .forms import InventoryRegistrationForm
import uuid
from datetime import datetime
from django import forms
from django.http import JsonResponse
from django.forms.utils import ErrorDict
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle,Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from inflect import engine 
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Notification, InventoryItem
from .forms import UpdateInventoryItemForm
from django.db.models import Q

def home(request):
    return render(request, 'home.html')

def bill(request):
    if request.method == 'POST':
        form = BillingForm(request.POST)
        if form.is_valid():
            patient_name = form.cleaned_data['patient_name']
            date_prescribed = form.cleaned_data['date_prescribed']
            prescribing_doctor = form.cleaned_data['prescribing_doctor']
            additional_notes = form.cleaned_data['additional_notes']
            medicines_and_quantities = form.cleaned_data['medicines_and_quantities']
            discount= form.cleaned_data['discount']
            symptoms = ""
            errors = ErrorDict()

            for idx, (medicine, quantity) in enumerate(medicines_and_quantities):
                try:
                    # Retrieve InventoryItem instance
                    medicine_instance = InventoryItem.objects.get(medicine_name=medicine)

                    # Check if the quantity is less than or equal to the available quantity in the inventory
                    if quantity > medicine_instance.quantity:
                         
                        errors[f'medicines_and_quantities-{idx}-quantity'] = [f"Insufficient quantity for {medicine} in the inventory."]
                        if medicine_instance.quantity ==0:
                            notification_message = f"The medicine {medicine} is out of stock."
                            create_notification(notification_message,medicine_instance.id )
                        form.add_error(None,f"Insufficient quantity for {medicine} in the inventory.")

                    # Check if the medicine is expired
                    if medicine_instance.expiry_date and medicine_instance.expiry_date < datetime.now().date():
                        errors[f'medicines_and_quantities-{idx}-medicine'] = [f"The medicine {medicine} has expired."]
                        form.add_error(None, f"The medicine {medicine} has expired.")

                    # Update symptoms
                    symptoms += medicine_instance.description + ","
                except InventoryItem.DoesNotExist:
                    # Handle the case where InventoryItem does not exist
                    errors[f'medicines_and_quantities-{idx}-medicine'] = [f"InventoryItem with medicine_name '{medicine}' does not exist."]
                    form.add_error(None, f"InventoryItem with medicine_name '{medicine}' does not exist.")

            # Remove the trailing comma from symptoms
            symptoms = symptoms.rstrip(',')

            if errors:
                # If there are errors, render the form with error messages
                form.add_error(None, "Please correct the following errors.")
                form._errors.update(errors)
                
            else:

                patients = Patient.objects.filter(name=patient_name, date_prescribed=date_prescribed,additional_notes=additional_notes,symptoms=symptoms)

                if patients.exists():
                    # If a patient with the same name and date_prescribed exists, use the first one
                    patient = patients.first()
                else:
                    # If no matching patient is found, create a new one
                    patient = Patient.objects.create(
                        name=patient_name,
                        date_prescribed=date_prescribed,
                        prescribing_doctor=prescribing_doctor,
                        additional_notes=additional_notes,
                        symptoms=symptoms
                        
                    )
                prefix="INV"
                # Create a unique identifier
                unique_id = str(uuid.uuid4()).replace("-", "")[:5]  # Adjust the length as needed

                # Include date information for additional context
                date_component = datetime.now().strftime("%y%m%d%H%M%S")

                # Combine the prefix, date, and unique identifier
                invoice_number = f"{prefix}{date_component}{unique_id}"

                    
                    

                billing = Billing(patient=patient,discount=discount,invoice_number=invoice_number )
                billing.save()

                total_amount = 0
                
                for inventory_item, quantity in medicines_and_quantities:
                    try:
                        # Change: Retrieve InventoryItem instance
                        inventory_item_instance = InventoryItem.objects.get(medicine_name=inventory_item)
                        if inventory_item_instance.quantity == quantity:
                            notification_message = f"The medicine {inventory_item_instance.medicine_name} is out of stock."
                            create_notification(notification_message,inventory_item_instance.id)

                        total_price = inventory_item_instance.price * quantity
                        BillingItem.objects.create(billing=billing, medicine=inventory_item_instance, quantity=quantity, total_price=total_price,invoice_number = invoice_number )
                    except InventoryItem.DoesNotExist:
                        # Handle the case where InventoryItem does not exist
                        print(f"InventoryItem with medicine_name '{inventory_item}' does not exist.")

                billing.save()

                return redirect('Bill', billing_id=billing.id)
    else:
        form = BillingForm()

    context = {'form': form}
    return render(request, 'bill.html', context)

def Bill(request, billing_id):
    
    billing = get_object_or_404(Billing, pk=billing_id)

    # Fetching billing items associated with the billing
    billing_items = billing.billingitem_set.all()

    # Fetching patient details from the associated Patient model
    patient = billing.patient

    context = {
        'billing': billing,
        'medicines': billing_items,
        'total_amount': billing.total_amount,
        'patient': patient,
        'Invoice': billing.invoice_number,
    }

    return render(request, 'bill print.html', context)
def get_medicine_details(request):
    medicine_name = request.GET.get('medicine', '')
    try:
        inventory_item = InventoryItem.objects.get(medicine_name=medicine_name)
        data = {
            'price': inventory_item.price,
            'quantity': inventory_item.quantity,  # You can include other details as needed
        }
        return JsonResponse(data)
    except InventoryItem.DoesNotExist:
        return JsonResponse({'error': 'Medicine not found'}, status=404)
def get_medicine_details_by_id(request, medicine_id):
    try:
        inventory_item = InventoryItem.objects.get(pk=medicine_id)
        data = {
            'medicine_name': inventory_item.medicine_name,
            'quantity': inventory_item.quantity,
            'manufacturer': inventory_item.manufacturer,
            'date_of_manufacture': str(inventory_item.date_of_manufacture),
            'expiry_date': str(inventory_item.expiry_date),
            'price': str(inventory_item.price),
            'cost_price': str(inventory_item.cost_price),
            'description': inventory_item.description,
            'batch_number': inventory_item.batch_number,
            'category': inventory_item.category,
        }
        return JsonResponse(data)
    except InventoryItem.DoesNotExist:
        return JsonResponse({'error': 'Medicine not found'}, status=404)

def inventory(request):
    if request.method == 'POST':
        form = InventoryRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory_list')
    else:
        form = InventoryRegistrationForm()

    return render(request, 'inventory.html', {'form': form})



def notification_view(request):
    # Remove expired notifications
    Notification.objects.filter(cleared=False, created_at__lt=timezone.now() - timezone.timedelta(hours=24)).delete()

    # Fetch non-expired and uncleared notifications
    uncleared_notifications = Notification.objects.filter(cleared=False)
    unique_messages = set()
    cleared_notifications = Notification.objects.filter(cleared=True)
    for notifications in cleared_notifications:
        notifications.delete()
        
        
        
    

    # Filter out duplicate notifications based on the message
    filtered_notifications = []
    for notification in uncleared_notifications:
        if notification.message not in unique_messages:
            filtered_notifications.append(notification)
            unique_messages.add(notification.message)
        else:
            # Remove duplicate notification from the database
            notification.delete()

    context = {
        'notifications': filtered_notifications,
    }

    return render(request, 'notification.html', context)
def clear_notification(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id)
    
    # Mark the notification as cleared
    notification.cleared = True
    notification.save()

    return HttpResponseRedirect(reverse('notification_view'))

def restock_view(request, medicine_id):
    medicine = get_object_or_404(InventoryItem, pk=medicine_id)

    if request.method == 'POST':
        form = UpdateInventoryItemForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()

            # Clear associated notification when restocking is done
            Notification.objects.filter(message__contains=medicine.medicine_name, cleared=False).delete()
            notification_message = f"The medicine {medicine.medicine_name} has been restocked."
            create_notification(notification_message, medicine.id)
            return redirect('inventory_list')

            return render(request, 'restock.html', {'form': form, 'inventory_item': medicine, 'medicine_id': medicine_id})
    else:
        form = UpdateInventoryItemForm(instance=medicine)

    return render(request, 'restock.html', {'form': form, 'inventory_item': medicine, 'medicine_id': medicine_id})




def create_notification(message, medicine_id):
    try:
        # Try to get an existing InventoryItem using medicine_id
        inventory_item = get_object_or_404(InventoryItem, pk=medicine_id)
    except InventoryItem.DoesNotExist:
        # If not found, return and do not create a notification
        print(f"Medicine with ID {medicine_id} not found. Notification not created.")
        return

    # Now you can safely use inventory_item in the rest of your code
    Notification.objects.create(message=message, medicine=inventory_item)


def inventory_list(request):
    inventory_list = InventoryItem.objects.all()  # Fetch all inventory items
    return render(request, 'inventory_list.html', {'inventory_list': inventory_list})
def checkdate():
    try:
        if date.objects.exists():
    # If records exist, get the count
            last_date_record = date .objects.latest('created_at')
            
            
        else:
            print("The DateModel is empty.")
    # Fetch the latest record based on the 'created_at' field
      

    # Do something with the last_date_record

    except DateModel.DoesNotExist:
        print("No records found in the DateModel.")
        
    
    




class GeneratePDF(View):
     
        def get(self, request, billing_id, *args, **kwargs):
            try:
                billing = Billing.objects.get(pk=billing_id)
            except Billing.DoesNotExist:
                return HttpResponse("Billing not found", status=404)

            pdf_file = BytesIO()
            p = SimpleDocTemplate(pdf_file, pagesize=letter)

            # Define styles
            styles = getSampleStyleSheet()
            header_style = styles['Heading2']
            body_style = styles['BodyText']

            # Create content elements
            elements = []

            # Header
            header_text = "MedBill - Invoice"
            elements.append(Paragraph(header_text, header_style))

            # Patient Information (Bold and Colored)
            patient_heading = f"<strong><font color='#17a2b8'>Patient Information</font></strong>"
            elements.append(Paragraph(patient_heading, body_style))
            patient_info = [
                f"<strong>Patient Name:</strong> {billing.patient.name}",
                f"<strong>Date Prescribed:</strong> {billing.patient.date_prescribed.strftime('%Y-%m-%d')}",
                f"<strong>Prescribing Doctor:</strong> {billing.patient.prescribing_doctor}",
                f"<strong>Additional Notes:</strong> {billing.patient.additional_notes}",
                f"<strong>Invoice Number:</strong> {billing.invoice_number}",
            ]
            elements.extend([Paragraph(info, body_style) for info in patient_info])

            # Line separator
            elements.append(Paragraph("<br/>", body_style))

            # Medicine Details Table (Bold and Colored)
            medicine_heading = f"<strong><font color='#17a2b8'>Medicine Details</font></strong>"
            elements.append(Paragraph(medicine_heading, body_style))

            # Medicine Details Table
            table_data = [
                ["Medicine Name", "Qty", "Manufacturer", "Unit Price", "Manufacturing Date", "Total Price", "Expiry Date"],
            ]

            for item in billing.billingitem_set.all():
                table_data.append([
                    item.medicine.medicine_name,
                    str(item.quantity),
                    item.medicine.manufacturer,
                    f"Rs {item.medicine.price}",
                    item.medicine.date_of_manufacture.strftime('%Y-%m-%d'),
                    f"Rs {item.total_price}",
                    item.medicine.expiry_date.strftime('%Y-%m-%d')
                ])

            # Table style
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#17a2b8")),  # Header background color
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Header text color
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center align all cells
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Add padding to the header cells
                ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add grid lines
            ])

            # Create the table
            medicine_table = Table(table_data, style=style)

            # Add elements to the PDF
            elements.append(medicine_table)

            # Net Amount (Sub Total)
            net_amount_text = f"<strong>Sub Total:</strong> Rs {billing.net_amount}"
            elements.append(Paragraph(net_amount_text, body_style))

            # Discount
            discount_text = f"<strong>Discount:</strong> {billing.discount}%"
            elements.append(Paragraph(discount_text, body_style))

            # Total Amount
            total_amount_text = f"<strong>Total Amount:</strong> Rs {billing.total_amount}"
            elements.append(Paragraph(total_amount_text, body_style))
            currency="Rupees"
            if billing.total_amount <= 1:
                currency="Rupee"
            # Total Amount in Words
            total_amount_words_text = f"<strong>Amount in Words (Total Amount):</strong> {self.get_amount_in_words(billing.total_amount)} {currency} only."
            elements.append(Paragraph(total_amount_words_text, body_style))
            item="Items"
            if billing.billingitem_set.count == 1:
                item="Item"

            # Total Items
            total_items_text = f"<strong>Total {item}:</strong> {billing.billingitem_set.count()}"
            elements.append(Paragraph(total_items_text, body_style))

            # Footer
            footer_text = "Thank you for choosing MedBill!"
            elements.append(Paragraph(footer_text, body_style))

            # Build the PDF
            p.build(elements)

            pdf_file.seek(0)
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'filename="invoice_{billing.patient.name}_{billing.patient.date_prescribed.strftime("%Y%m%d")}.pdf"'
            return response

        def get_amount_in_words(self, amount):
            p = engine()
            return p.number_to_words(amount, andword='and', zero='zero')
