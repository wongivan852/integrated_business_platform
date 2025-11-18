# management/commands/load_sample_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from crm.models import Customer, Course, Conference, Enrollment
import random

class Command(BaseCommand):
    help = 'Load sample data for testing the CRM system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customers',
            type=int,
            default=50,
            help='Number of sample customers to create'
        )
        parser.add_argument(
            '--courses',
            type=int,
            default=10,
            help='Number of sample courses to create'
        )

    def handle(self, *args, **options):
        self.stdout.write('Loading sample data...')
        
        customers_count = options['customers']
        courses_count = options['courses']
        
        self.create_sample_customers(customers_count)
        self.create_sample_courses(courses_count)
        self.create_sample_conferences()
        self.create_sample_enrollments()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded sample data: '
                f'{customers_count} customers, {courses_count} courses'
            )
        )

    def create_sample_customers(self, count):
        sample_customers = [
            {
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'email_primary': 'alice.johnson@email.com',
                'phone_primary': '+1234567890',
                'whatsapp_number': '+1234567890',
                'customer_type': 'individual',
                'status': 'active',
                'company_primary': 'Tech Corp',
                'position_primary': 'Software Engineer',
                'preferred_communication_method': 'email',
                'interests': 'Python, Data Science, Machine Learning'
            },
            {
                'first_name': 'Bob',
                'last_name': 'Smith',
                'email_primary': 'bob.smith@email.com',
                'phone_primary': '+1234567891',
                'whatsapp_number': '+1234567891',
                'customer_type': 'corporate',
                'status': 'active',
                'company_primary': 'Innovation Inc',
                'position_primary': 'CTO',
                'preferred_communication_method': 'whatsapp',
                'interests': 'Leadership, Technology Strategy'
            },
            {
                'first_name': 'Carol',
                'last_name': 'Williams',
                'email_primary': 'carol.williams@email.com',
                'phone_primary': '+1234567892',
                'whatsapp_number': '+1234567892',
                'customer_type': 'student',
                'status': 'active',
                'company_primary': 'University of Technology',
                'position_primary': 'Graduate Student',
                'preferred_communication_method': 'email',
                'interests': 'Web Development, UX Design'
            },
            {
                'first_name': 'David',
                'last_name': 'Brown',
                'email_primary': 'david.brown@email.com',
                'phone_primary': '+1234567893',
                'whatsapp_number': '+1234567893',
                'customer_type': 'instructor',
                'status': 'active',
                'company_primary': 'Learning Institute',
                'position_primary': 'Senior Instructor',
                'preferred_communication_method': 'phone',
                'interests': 'Training, Education Technology'
            },
            {
                'first_name': 'Emma',
                'last_name': 'Davis',
                'email_primary': 'emma.davis@email.com',
                'phone_primary': '+1234567894',
                'whatsapp_number': '+1234567894',
                'customer_type': 'youtuber',
                'status': 'prospect',
                'youtube_handle': 'emmadavis_tech',
                'youtube_channel_url': 'https://youtube.com/@emmadavis_tech',
                'preferred_communication_method': 'email',
                'interests': 'Content Creation, Video Production'
            },
            {
                'first_name': 'Frank',
                'last_name': 'Miller',
                'email_primary': 'frank.miller@email.com',
                'phone_primary': '+1234567895',
                'whatsapp_number': '+1234567895',
                'customer_type': 'individual',
                'status': 'active',
                'company_primary': 'Startup Solutions',
                'position_primary': 'Product Manager',
                'preferred_communication_method': 'whatsapp',
                'interests': 'Product Management, Agile'
            }
        ]
        
        # Create base customers
        for customer_data in sample_customers:
            customer, created = Customer.objects.get_or_create(
                email_primary=customer_data['email_primary'],
                defaults=customer_data
            )
            if created:
                self.stdout.write(f'Created customer: {customer.first_name} {customer.last_name}')

    def create_sample_courses(self, count):
        sample_courses = [
            {
                'title': 'Python Programming Bootcamp',
                'description': 'Comprehensive Python programming course covering basics to advanced concepts',
                'course_type': 'online',
                'duration_hours': 40,
                'price': 299.00,
                'max_participants': 30,
                'start_date': timezone.now() + timedelta(days=30),
                'end_date': timezone.now() + timedelta(days=45),
                'registration_deadline': timezone.now() + timedelta(days=25)
            },
            {
                'title': 'Data Science Fundamentals',
                'description': 'Learn data analysis, visualization, and machine learning basics',
                'course_type': 'hybrid',
                'duration_hours': 60,
                'price': 499.00,
                'max_participants': 25,
                'start_date': timezone.now() + timedelta(days=45),
                'end_date': timezone.now() + timedelta(days=75),
                'registration_deadline': timezone.now() + timedelta(days=40)
            },
            {
                'title': 'Web Development Workshop',
                'description': 'HTML, CSS, JavaScript and modern web frameworks',
                'course_type': 'workshop',
                'duration_hours': 24,
                'price': 199.00,
                'max_participants': 20,
                'start_date': timezone.now() + timedelta(days=20),
                'end_date': timezone.now() + timedelta(days=22),
                'registration_deadline': timezone.now() + timedelta(days=15)
            },
            {
                'title': 'Digital Marketing Seminar',
                'description': 'Social media marketing, content strategy, and analytics',
                'course_type': 'seminar',
                'duration_hours': 8,
                'price': 99.00,
                'max_participants': 50,
                'start_date': timezone.now() + timedelta(days=10),
                'end_date': timezone.now() + timedelta(days=10),
                'registration_deadline': timezone.now() + timedelta(days=7)
            },
            {
                'title': 'Leadership Excellence Program',
                'description': 'Advanced leadership skills for managers and executives',
                'course_type': 'offline',
                'duration_hours': 32,
                'price': 799.00,
                'max_participants': 15,
                'start_date': timezone.now() + timedelta(days=60),
                'end_date': timezone.now() + timedelta(days=65),
                'registration_deadline': timezone.now() + timedelta(days=50)
            }
        ]
        
        for course_data in sample_courses:
            course, created = Course.objects.get_or_create(
                title=course_data['title'],
                defaults=course_data
            )
            if created:
                self.stdout.write(f'Created course: {course.title}')

    def create_sample_conferences(self):
        sample_conferences = [
            {
                'name': 'Tech Innovation Summit 2025',
                'description': 'Annual technology innovation conference featuring industry leaders',
                'venue': 'Grand Convention Center, Downtown',
                'start_date': timezone.now() + timedelta(days=90),
                'end_date': timezone.now() + timedelta(days=92),
                'registration_fee': 299.00,
                'max_attendees': 500
            },
            {
                'name': 'Digital Transformation Workshop',
                'description': 'Interactive workshop on digital transformation strategies',
                'venue': 'Business Hub Conference Room',
                'start_date': timezone.now() + timedelta(days=35),
                'end_date': timezone.now() + timedelta(days=35),
                'registration_fee': 149.00,
                'max_attendees': 100
            },
            {
                'name': 'Future of Learning Conference',
                'description': 'Exploring trends in education technology and online learning',
                'venue': 'Education Center Auditorium',
                'start_date': timezone.now() + timedelta(days=120),
                'end_date': timezone.now() + timedelta(days=121),
                'registration_fee': 199.00,
                'max_attendees': 300
            }
        ]
        
        for conference_data in sample_conferences:
            conference, created = Conference.objects.get_or_create(
                name=conference_data['name'],
                defaults=conference_data
            )
            if created:
                self.stdout.write(f'Created conference: {conference.name}')

    def create_sample_enrollments(self):
        customers = Customer.objects.all()
        courses = Course.objects.all()
        
        if customers and courses:
            # Create some sample enrollments
            enrollments_data = [
                (customers[0], courses[0], 'confirmed', 'paid'),  # Alice -> Python Bootcamp
                (customers[1], courses[1], 'registered', 'pending'),  # Bob -> Data Science
                (customers[2], courses[2], 'confirmed', 'paid'),  # Carol -> Web Development
                (customers[3], courses[3], 'completed', 'paid'),  # David -> Digital Marketing
                (customers[0], courses[3], 'registered', 'pending'),  # Alice -> Digital Marketing
            ]
            
            for customer, course, status, payment_status in enrollments_data:
                if customer and course:
                    enrollment, created = Enrollment.objects.get_or_create(
                        customer=customer,
                        course=course,
                        defaults={
                            'status': status,
                            'payment_status': payment_status,
                            'notes': f'Sample enrollment for {customer.first_name}'
                        }
                    )
                    if created:
                        self.stdout.write(f'Created enrollment: {customer.first_name} -> {course.title}')
