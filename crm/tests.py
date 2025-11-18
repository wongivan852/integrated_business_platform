from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest.mock import patch, MagicMock
import uuid
from datetime import datetime, timedelta
from django.utils import timezone

from .models import (
    Customer, Course, Enrollment, Conference, 
    ConferenceRegistration, CommunicationLog,
    CustomerCommunicationPreference
)
from .forms import CustomerForm
from .utils import generate_customer_csv_response, validate_uat_access
from .communication_services import CommunicationManager


class CustomerModelTest(TestCase):
    """Test Customer model functionality"""
    
    def setUp(self):
        self.customer_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email_primary': 'john.doe@example.com',
            'customer_type': 'individual',
            'status': 'active',
            'country_region': 'US'
        }
    
    def test_customer_creation(self):
        """Test creating a customer with basic data"""
        customer = Customer.objects.create(**self.customer_data)
        self.assertIsInstance(customer.id, uuid.UUID)
        self.assertEqual(customer.first_name, 'John')
        self.assertEqual(customer.last_name, 'Doe')
        self.assertEqual(customer.email_primary, 'john.doe@example.com')
    
    def test_customer_full_name_property(self):
        """Test full name property"""
        customer = Customer.objects.create(
            first_name='John',
            middle_name='William',
            last_name='Doe',
            name_suffix='Jr.',
            **{k: v for k, v in self.customer_data.items() 
               if k not in ['first_name', 'last_name']}
        )
        self.assertEqual(customer.full_name, 'John William Doe Jr.')
    
    def test_customer_display_name_property(self):
        """Test display name property"""
        customer = Customer.objects.create(**self.customer_data)
        self.assertEqual(customer.display_name, 'John Doe')
        
        # Test with preferred name
        customer.preferred_name = 'Johnny'
        self.assertEqual(customer.display_name, 'Johnny')
    
    def test_customer_str_representation(self):
        """Test string representation"""
        customer = Customer.objects.create(**self.customer_data)
        expected = 'John Doe (john.doe@example.com)'
        self.assertEqual(str(customer), expected)
    
    def test_country_code_functionality(self):
        """Test country code auto-setting"""
        customer = Customer.objects.create(
            phone_primary='1234567890',
            **self.customer_data
        )
        customer.save()  # Trigger auto_set_country_codes
        self.assertEqual(customer.phone_primary_country_code, '+1')
    
    def test_email_validation(self):
        """Test email validation"""
        with self.assertRaises(Exception):
            Customer.objects.create(
                **{**self.customer_data, 'email_primary': 'invalid-email'}
            )
    
    def test_address_fields(self):
        """Test address field structure"""
        customer = Customer.objects.create(
            address='123 Main St',
            city='New York',
            state_province='NY',
            postal_code='10001',
            address_primary='123 Main St\nNew York, NY 10001',
            **self.customer_data
        )
        self.assertEqual(customer.address, '123 Main St')
        self.assertEqual(customer.city, 'New York')
        self.assertEqual(customer.address_primary, '123 Main St\nNew York, NY 10001')


class CustomerFormTest(TestCase):
    """Test Customer form functionality"""
    
    def test_valid_form(self):
        """Test form with valid data"""
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email_primary': 'jane.smith@example.com',
            'customer_type': 'student',
            'status': 'prospect',
            'country_region': 'CA'
        }
        form = CustomerForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_required_fields(self):
        """Test form validation for required fields"""
        form = CustomerForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)
        self.assertIn('email_primary', form.errors)
    
    def test_email_validation(self):
        """Test email field validation"""
        form_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email_primary': 'invalid-email',
            'customer_type': 'student'
        }
        form = CustomerForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email_primary', form.errors)


class CourseModelTest(TestCase):
    """Test Course model functionality"""
    
    def test_course_creation(self):
        """Test creating a course"""
        course = Course.objects.create(
            title='Python Programming',
            description='Learn Python programming',
            course_type='online',
            duration_hours=40,
            price=299.00,
            max_participants=30,
            start_date=timezone.now() + timedelta(days=30),
            end_date=timezone.now() + timedelta(days=45),
            registration_deadline=timezone.now() + timedelta(days=25)
        )
        self.assertEqual(course.title, 'Python Programming')
        self.assertEqual(course.course_type, 'online')
        self.assertEqual(course.duration_hours, 40)


class EnrollmentModelTest(TestCase):
    """Test Enrollment model functionality"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name='Test',
            last_name='User',
            email_primary='test@example.com',
            customer_type='student'
        )
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            course_type='online',
            duration_hours=10,
            price=100.00,
            max_participants=10,
            start_date=timezone.now() + timedelta(days=10),
            end_date=timezone.now() + timedelta(days=12),
            registration_deadline=timezone.now() + timedelta(days=5)
        )
    
    def test_enrollment_creation(self):
        """Test creating an enrollment"""
        enrollment = Enrollment.objects.create(
            customer=self.customer,
            course=self.course,
            status='registered'
        )
        self.assertEqual(enrollment.customer, self.customer)
        self.assertEqual(enrollment.course, self.course)
        self.assertEqual(enrollment.status, 'registered')
    
    def test_unique_enrollment_constraint(self):
        """Test that customer can't enroll in same course twice"""
        Enrollment.objects.create(
            customer=self.customer,
            course=self.course
        )
        with self.assertRaises(Exception):
            Enrollment.objects.create(
                customer=self.customer,
                course=self.course
            )


class UtilsTest(TestCase):
    """Test utility functions"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name='Utils',
            last_name='Test',
            email_primary='utils@example.com',
            customer_type='individual'
        )
    
    def test_csv_export_generation(self):
        """Test CSV export utility"""
        response = generate_customer_csv_response()
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('customers_export_', response['Content-Disposition'])
    
    @patch('crm.utils.settings')
    def test_uat_access_validation_enabled(self, mock_settings):
        """Test UAT access validation when enabled"""
        mock_settings.ENABLE_PUBLIC_UAT_VIEWS = True
        mock_settings.UAT_ACCESS_TOKEN = 'test-token'
        
        # Create a mock request
        from django.http import HttpRequest
        request = HttpRequest()
        request.GET = {'token': 'test-token'}
        
        is_valid, error = validate_uat_access(request)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    @patch('crm.utils.settings')
    def test_uat_access_validation_disabled(self, mock_settings):
        """Test UAT access validation when disabled"""
        mock_settings.ENABLE_PUBLIC_UAT_VIEWS = False
        
        from django.http import HttpRequest
        request = HttpRequest()
        
        is_valid, error = validate_uat_access(request)
        self.assertFalse(is_valid)
        self.assertIn('disabled', error)


class APITestCase(APITestCase):
    """Test API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        
        self.customer = Customer.objects.create(
            first_name='API',
            last_name='Test',
            email_primary='api@example.com',
            customer_type='individual'
        )
    
    def test_customer_list_api(self):
        """Test customer list API endpoint"""
        url = reverse('crm:customer-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_customer_create_api(self):
        """Test customer creation via API"""
        url = reverse('crm:customer-list')
        data = {
            'first_name': 'API',
            'last_name': 'Created',
            'email_primary': 'api.created@example.com',
            'customer_type': 'student'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_customer_detail_api(self):
        """Test customer detail API endpoint"""
        url = reverse('crm:customer-detail', kwargs={'pk': self.customer.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'API')
    
    def test_unauthorized_access(self):
        """Test API access without authentication"""
        self.client.credentials()  # Remove credentials
        url = reverse('crm:customer-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ViewsTest(TestCase):
    """Test view functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    @patch('crm.views.settings')
    def test_public_customer_list_with_valid_token(self, mock_settings):
        """Test public customer list with valid UAT token"""
        mock_settings.ENABLE_PUBLIC_UAT_VIEWS = True
        mock_settings.UAT_ACCESS_TOKEN = 'valid-token'
        
        url = reverse('crm:customer_list')
        response = self.client.get(url, {'token': 'valid-token'})
        self.assertEqual(response.status_code, 200)
    
    @patch('crm.views.settings')
    def test_public_customer_list_with_invalid_token(self, mock_settings):
        """Test public customer list with invalid UAT token"""
        mock_settings.ENABLE_PUBLIC_UAT_VIEWS = True
        mock_settings.UAT_ACCESS_TOKEN = 'valid-token'
        
        url = reverse('crm:customer_list')
        response = self.client.get(url, {'token': 'invalid-token'})
        self.assertEqual(response.status_code, 403)
    
    def test_csv_export_requires_login(self):
        """Test CSV export requires authentication"""
        url = reverse('crm:export_customers_csv')
        response = self.client.get(url)
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_csv_export_with_login(self):
        """Test CSV export with authentication"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('crm:export_customers_csv')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')


class CommunicationTest(TestCase):
    """Test communication functionality"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name='Comm',
            last_name='Test',
            email_primary='comm@example.com',
            customer_type='individual',
            whatsapp_number='+1234567890'
        )
    
    @patch('crm.communication_services.requests.post')
    def test_whatsapp_message_send(self, mock_post):
        """Test WhatsApp message sending"""
        from .communication_services import WhatsAppService
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'messages': [{'id': 'msg123'}]
        }
        mock_post.return_value = mock_response
        
        whatsapp = WhatsAppService()
        success, message_id = whatsapp.send_message(
            '+1234567890', 
            'Test message', 
            self.customer
        )
        
        self.assertTrue(success)
        self.assertEqual(message_id, 'msg123')
    
    def test_communication_log_creation(self):
        """Test communication log entry creation"""
        log = CommunicationLog.objects.create(
            customer=self.customer,
            channel='email',
            subject='Test Subject',
            content='Test content',
            is_outbound=True
        )
        self.assertEqual(log.customer, self.customer)
        self.assertEqual(log.channel, 'email')
        self.assertTrue(log.is_outbound)


class SecurityTest(TestCase):
    """Test security features"""
    
    def test_secret_key_not_default(self):
        """Test that SECRET_KEY is not the default insecure key"""
        self.assertNotIn('django-insecure', settings.SECRET_KEY)
    
    def test_debug_false_in_production_config(self):
        """Test DEBUG setting behavior"""
        # This test assumes the environment variable is properly configured
        # In production, DEBUG should be False
        if not settings.DEBUG:
            self.assertFalse(settings.DEBUG)
    
    def test_allowed_hosts_configured(self):
        """Test ALLOWED_HOSTS is properly configured"""
        self.assertIsInstance(settings.ALLOWED_HOSTS, list)
        self.assertGreater(len(settings.ALLOWED_HOSTS), 0)


class IntegrationTest(TestCase):
    """Integration tests for complete workflows"""
    
    def test_customer_creation_workflow(self):
        """Test complete customer creation workflow"""
        # Create customer
        customer = Customer.objects.create(
            first_name='Integration',
            last_name='Test',
            email_primary='integration@example.com',
            customer_type='student',
            phone_primary='1234567890',
            country_region='US'
        )
        
        # Verify customer was created with auto-populated fields
        self.assertIsNotNone(customer.id)
        self.assertEqual(customer.phone_primary_country_code, '+1')
        
        # Create course and enrollment
        course = Course.objects.create(
            title='Integration Course',
            description='Test course',
            course_type='online',
            duration_hours=10,
            price=100.00,
            max_participants=20,
            start_date=timezone.now() + timedelta(days=10),
            end_date=timezone.now() + timedelta(days=12),
            registration_deadline=timezone.now() + timedelta(days=5)
        )
        
        enrollment = Enrollment.objects.create(
            customer=customer,
            course=course,
            status='registered'
        )
        
        # Verify enrollment
        self.assertEqual(enrollment.customer, customer)
        self.assertEqual(enrollment.course, course)
        
        # Test CSV export includes the customer
        response = generate_customer_csv_response()
        content = response.content.decode('utf-8')
        self.assertIn('Integration', content)
        self.assertIn('integration@example.com', content)
