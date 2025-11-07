from django.urls import path
from . import views

app_name = 'quotations'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Quotations
    path('quotations/', views.quotation_list, name='quotation_list'),
    path('quotations/create/', views.create_quotation, name='create_quotation'),
    path('quotations/<int:quotation_id>/edit/', views.edit_quotation, name='edit_quotation'),

    # Customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.create_customer, name='create_customer'),

    # Services
    path('services/', views.service_list, name='service_list'),
    path('services/create/', views.create_service, name='create_service'),
]