from django.urls import path
from medbill import views
urlpatterns=[
    path('',views.home,name='home'),
    path('bill',views.bill,name='bill'),
    path('Bill_print/<int:billing_id>/',views.Bill,name='Bill'),
    path('inventory registration',views.inventory,name='inventory registration'),
    path('generate_pdf/<int:billing_id>/', views.GeneratePDF.as_view(), name='generate_pdf'),
    path('api/get_medicine_details/', views.get_medicine_details, name='get_medicine_details'),
     path('api/get_medicine_details/<int:medicine_id>/', views.get_medicine_details_by_id, name='get_medicine_details_by_id'),
    path('restock/<int:medicine_id>/', views.restock_view, name='restock_view'),
    path('notifications/', views.notification_view, name='notification_view'),
    path('clear_notification/<int:notification_id>/', views.clear_notification, name='clear_notification'),
    path('inventory-list/', views.inventory_list, name='inventory_list'),
    ]