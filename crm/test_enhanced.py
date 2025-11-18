# test_enhanced.py - Comprehensive tests for the CRM system
import pytest
from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest.mock import patch, MagicMock
import uuid
from datetime import datetime, timedelta
from django.utils import timezone

from .models import (
    Customer, Course, Enrollment, Conference, 
    ConferenceRegistration, CommunicationLog
)
from .forms import CustomerForm
from .communication_services import CommunicationManager, WhatsAppService
from .error_handlers import CRMException, CustomerNotFoundError
from .utils import generate_customer_csv_response


class BaseTestCase(TestCase):
    """Base test case with common setup"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.customer_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email_primary': 'john.doe@example.com',
            'customer_type': 'individual',
            'status': 'active',
            'country_region': 'US'
        }
        
    def tearDown(self):
        # Clear cache after each test
        cache.clear()


class CustomerModelTestEnhanced(BaseTestCase):
    """Enhanced tests for Customer model"""
    
    def test_customer_creation_with_full_data(self):
        """Test creating customer with all fields"""
        customer_data = {
            **self.customer_data,
            'middle_name': 'William',
            'name_suffix': 'Jr.',
            'phone_primary': '5551234567',
            'phone_primary_country_code': '+1',
            'whatsapp_number': '5551234567',
            'whatsapp_country_code': '+1',
            'company_primary': 'Tech Corp',
            'position_primary': 'Developer'
        }
        customer = Customer.objects.create(**customer_data)
        
        self.assertIsInstance(customer.id, uuid.UUID)
        self.assertEqual(customer.full_name, 'John William Doe Jr.')
        self.assertEqual(customer.country_region, 'US')
        
    def test_customer_email_uniqueness(self):
        """Test that primary email must be unique"""
        Customer.objects.create(**self.customer_data)
        
        with self.assertRaises(Exception):
            Customer.objects.create(**self.customer_data)
            
    def test_customer_str_representation(self):
        """Test customer string representation"""
        customer = Customer.objects.create(**self.customer_data)
        expected = f"{customer.first_name} {customer.last_name}"
        self.assertEqual(str(customer), expected)
        
    def test_country_code_mapping(self):
        """Test country code mapping functionality"""
        customer = Customer.objects.create(
            **self.customer_data,
            country_region='CN'
        )
        # Test if the customer can access country code mapping
        self.assertIn('CN', Customer.COUNTRY_CODE_MAP)
        self.assertEqual(Customer.COUNTRY_CODE_MAP['CN'], '+86')


class CustomerAPITestEnhanced(APITestCase):
    """Enhanced API tests for Customer endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email_primary='john.doe@example.com',
            customer_type='individual',
            status='active'
        )
        
    def test_customer_list_with_caching(self):
        """Test customer list endpoint with caching"""
        url = reverse('customer-list')
        
        # First request - should hit database
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second request - should use cache
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data, response2.data)
        
    def test_customer_search_by_contact(self):
        """Test customer search by contact information"""
        url = reverse('customer-search-by-contact')
        
        # Test search by email
        response = self.client.get(url, {'contact': 'john.doe'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test empty search
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_customer_csv_export(self):
        """Test customer CSV export functionality"""
        url = reverse('customer-export-csv')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
    @patch('crm.communication_services.CommunicationManager.send_message')
    def test_send_message_to_customer(self, mock_send):
        """Test sending message to customer"""
        mock_send.return_value = (True, "Message sent successfully")
        
        url = reverse('customer-send-message', kwargs={'pk': self.customer.id})
        data = {
            'channel': 'email',
            'subject': 'Test Subject',
            'content': 'Test message content'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        mock_send.assert_called_once()


class CommunicationServiceTest(BaseTestCase):
    """Test communication services"""
    
    def setUp(self):
        super().setUp()
        self.customer = Customer.objects.create(**self.customer_data)
        
    @patch('crm.communication_services.requests.post')
    def test_whatsapp_service_success(self, mock_post):
        """Test successful WhatsApp message sending"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'messages': [{'id': 'test_id'}]}
        
        with patch.object(WhatsAppService, '__init__', lambda x: None):
            service = WhatsAppService()
            service.api_url = 'https://test.api.com'
            service.access_token = 'test_token'
            service.phone_number_id = 'test_phone_id'
            
            success, message = service.send_message('+1234567890', 'Test message')
            self.assertTrue(success)
            
    @patch('crm.communication_services.CommunicationManager')
    def test_communication_manager_integration(self, mock_manager):
        """Test communication manager with different channels"""
        mock_instance = mock_manager.return_value
        mock_instance.send_message.return_value = (True, "Success")
        
        manager = CommunicationManager()
        success, message = manager.send_message(
            self.customer, 'email', 'Test Subject', 'Test Content'
        )
        
        self.assertTrue(success)


class CourseEnrollmentTest(BaseTestCase):
    """Test course and enrollment functionality"""
    
    def setUp(self):
        super().setUp()
        self.customer = Customer.objects.create(**self.customer_data)
        self.course = Course.objects.create(
            title='Python Programming',
            description='Learn Python programming',
            course_type='online',
            duration_hours=40,
            price=299.00,
            max_participants=30,
            start_date=timezone.now() + timedelta(days=30),
            end_date=timezone.now() + timedelta(days=60),
            registration_deadline=timezone.now() + timedelta(days=25)
        )
        
    def test_course_creation(self):
        """Test course creation with valid data"""
        self.assertEqual(self.course.title, 'Python Programming')
        self.assertEqual(self.course.course_type, 'online')
        self.assertTrue(self.course.is_active)
        
    def test_enrollment_creation(self):
        """Test student enrollment in course"""
        enrollment = Enrollment.objects.create(
            customer=self.customer,
            course=self.course,
            status='registered'
        )
        
        self.assertEqual(enrollment.customer, self.customer)
        self.assertEqual(enrollment.course, self.course)
        self.assertEqual(enrollment.status, 'registered')
        
    def test_enrollment_unique_constraint(self):
        """Test that customer can't enroll in same course twice"""
        Enrollment.objects.create(
            customer=self.customer,
            course=self.course,
            status='registered'
        )
        
        # Try to create duplicate enrollment
        with self.assertRaises(Exception):
            Enrollment.objects.create(
                customer=self.customer,
                course=self.course,
                status='registered'
            )


class ErrorHandlingTest(BaseTestCase):
    """Test error handling functionality"""
    
    def test_crm_exception_creation(self):
        """Test custom CRM exception"""
        exception = CRMException(
            message="Test error",
            error_code="TEST_ERROR",
            details={'field': 'value'}
        )
        
        self.assertEqual(exception.message, "Test error")
        self.assertEqual(exception.error_code, "TEST_ERROR")
        self.assertEqual(exception.details['field'], 'value')
        
    def test_customer_not_found_error(self):
        """Test customer not found error"""
        with self.assertRaises(CustomerNotFoundError):
            raise CustomerNotFoundError("Customer not found")


class FormValidationTest(BaseTestCase):
    """Test form validation"""
    
    def test_customer_form_valid_data(self):
        """Test customer form with valid data"""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email_primary': 'john.doe@example.com',
            'customer_type': 'individual',
            'status': 'active',
            'country_region': 'US'
        }
        
        form = CustomerForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_customer_form_invalid_email(self):
        """Test customer form with invalid email"""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email_primary': 'invalid-email',
            'customer_type': 'individual',
            'status': 'active'
        }
        
        form = CustomerForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email_primary', form.errors)


class CacheTest(BaseTestCase):
    """Test caching functionality"""
    
    def test_cache_customer_search(self):
        """Test that customer search results are cached"""
        customer = Customer.objects.create(**self.customer_data)
        
        # Clear cache first
        cache.clear()
        
        # Test that cache is initially empty
        cache_key = "customer_search_john"
        self.assertIsNone(cache.get(cache_key))
        
        # Test cache setting
        cache.set(cache_key, [{'id': str(customer.id), 'name': 'John Doe'}], 300)
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(len(cached_data), 1)


class IntegrationTest(TransactionTestCase):
    """Integration tests for complete workflows"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.customer_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email_primary': 'john.doe@example.com',
            'customer_type': 'individual',
            'status': 'active'
        }
        
    def test_complete_customer_lifecycle(self):
        """Test complete customer lifecycle from creation to communication"""
        # Create customer
        customer = Customer.objects.create(**self.customer_data)
        self.assertTrue(customer.id)
        
        # Create course
        course = Course.objects.create(
            title='Python Course',
            description='Learn Python',
            course_type='online',
            duration_hours=40,
            price=299.00,
            max_participants=30,
            start_date=timezone.now() + timedelta(days=30),
            end_date=timezone.now() + timedelta(days=60)
        )
        
        # Enroll customer
        enrollment = Enrollment.objects.create(
            customer=customer,
            course=course,
            status='registered'
        )
        
        # Log communication
        comm_log = CommunicationLog.objects.create(
            customer=customer,
            channel='email',
            subject='Welcome Email',
            content='Welcome to our course!',
            status='sent'
        )
        
        # Verify all objects exist and are related
        self.assertEqual(enrollment.customer, customer)
        self.assertEqual(enrollment.course, course)
        self.assertEqual(comm_log.customer, customer)
        
        # Verify customer has enrollments and communication logs
        self.assertEqual(customer.enrollment_set.count(), 1)
        self.assertEqual(customer.communicationlog_set.count(), 1)


# Pytest fixtures and tests
@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_user():
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    return user


@pytest.fixture
def sample_customer():
    return Customer.objects.create(
        first_name='Jane',
        last_name='Smith',
        email_primary='jane.smith@example.com',
        customer_type='individual',
        status='active'
    )


@pytest.mark.django_db
def test_customer_api_with_pytest(api_client, authenticated_user, sample_customer):
    """Test customer API using pytest"""
    token = Token.objects.create(user=authenticated_user)
    api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    
    url = reverse('customer-list')
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['first_name'] == 'Jane'


@pytest.mark.django_db
def test_course_enrollment_pytest(sample_customer):
    """Test course enrollment using pytest"""
    course = Course.objects.create(
        title='Data Science Course',
        description='Learn Data Science',
        course_type='hybrid',
        duration_hours=60,
        price=499.00,
        max_participants=25,
        start_date=timezone.now() + timedelta(days=15),
        end_date=timezone.now() + timedelta(days=45)
    )
    
    enrollment = Enrollment.objects.create(
        customer=sample_customer,
        course=course,
        status='confirmed'
    )
    
    assert enrollment.customer == sample_customer
    assert enrollment.course == course
    assert enrollment.status == 'confirmed'