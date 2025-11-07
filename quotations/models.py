from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Customer(models.Model):
    """Customer model for quotations"""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.company})" if self.company else self.name

    class Meta:
        ordering = ['name']


class Service(models.Model):
    """Service/Product that can be quoted"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, default='each')  # e.g., 'each', 'hour', 'day'
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Quotation(models.Model):
    """Main quotation model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]

    quotation_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Financial fields
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    valid_until = models.DateField(null=True, blank=True)

    # User tracking
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_quotations')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='updated_quotations')

    def __str__(self):
        return f"{self.quotation_number} - {self.customer.name}"

    def calculate_totals(self):
        """Calculate subtotal, tax, and total"""
        self.subtotal = sum(item.total for item in self.items.all())
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.total = self.subtotal + self.tax_amount
        self.save()

    def is_expired(self):
        """Check if quotation is expired"""
        if self.valid_until:
            return timezone.now().date() > self.valid_until
        return False

    class Meta:
        ordering = ['-created_at']


class QuotationItem(models.Model):
    """Individual items in a quotation"""
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    description = models.TextField(blank=True)  # Override service description if needed
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    order = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        """Calculate total before saving"""
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Update quotation totals
        self.quotation.calculate_totals()

    def __str__(self):
        return f"{self.service.name} x {self.quantity}"

    class Meta:
        ordering = ['order', 'id']


class QuotationHistory(models.Model):
    """Track quotation status changes"""
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.quotation.quotation_number} - {self.status}"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Quotation histories'
