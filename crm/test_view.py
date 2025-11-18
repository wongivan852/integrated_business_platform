from django.http import HttpResponse
from django.shortcuts import render
from .forms import CustomerForm

def test_country_code_form(request):
    """Simple test view for country code functionality"""
    form = CustomerForm()
    return render(request, 'crm/test_country_code_form.html', {'form': form})
