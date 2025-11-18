# warm_cache.py - Management command to pre-warm cache for UAT
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
from crm.cache_utils import CacheWarmer
from crm.models import Customer, Course, Enrollment
import logging

logger = logging.getLogger('crm.performance')

class Command(BaseCommand):
    help = 'Pre-warm cache with frequently accessed data for UAT performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-first',
            action='store_true',
            help='Clear existing cache before warming',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed cache warming progress',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        if options['clear_first']:
            self.stdout.write('Clearing existing cache...')
            cache.clear()
            if verbose:
                self.stdout.write(self.style.SUCCESS('Cache cleared successfully'))

        self.stdout.write('Starting cache warming process...')
        
        try:
            # Warm customer statistics
            if verbose:
                self.stdout.write('Warming customer statistics...')
            CacheWarmer.warm_customer_stats()
            
            # Warm country codes
            if verbose:
                self.stdout.write('Warming country codes...')
            CacheWarmer.warm_country_codes()
            
            # Warm recent customers for dashboard
            if verbose:
                self.stdout.write('Warming recent customers...')
            recent_customers = list(Customer.objects.select_related().only(
                'id', 'first_name', 'last_name', 'email_primary', 'created_at'
            ).order_by('-created_at')[:10].values())
            cache.set('recent_customers_list', recent_customers, settings.CACHE_TTL['dashboard_stats'])
            
            # Warm active courses
            if verbose:
                self.stdout.write('Warming active courses...')
            active_courses = list(Course.objects.filter(is_active=True).only(
                'id', 'title', 'course_type', 'start_date', 'price'
            ).values())
            cache.set('active_courses_list', active_courses, settings.CACHE_TTL['course_list'])
            
            # Warm enrollment statistics
            if verbose:
                self.stdout.write('Warming enrollment statistics...')
            enrollment_stats = {
                'total': Enrollment.objects.count(),
                'by_status': {}
            }
            for status, _ in Enrollment.STATUS_CHOICES:
                enrollment_stats['by_status'][status] = Enrollment.objects.filter(status=status).count()
            cache.set('enrollment_stats', enrollment_stats, settings.CACHE_TTL['dashboard_stats'])
            
            # Warm customer type distribution
            if verbose:
                self.stdout.write('Warming customer type distribution...')
            customer_type_stats = {}
            for customer_type, _ in Customer.CUSTOMER_TYPES:
                customer_type_stats[customer_type] = Customer.objects.filter(customer_type=customer_type).count()
            cache.set('customer_type_distribution', customer_type_stats, settings.CACHE_TTL['dashboard_stats'])
            
            # Pre-cache common search patterns (last 7 days of activity)
            if verbose:
                self.stdout.write('Pre-caching common search patterns...')
            from django.utils import timezone
            from datetime import timedelta
            
            week_ago = timezone.now() - timedelta(days=7)
            recent_customer_emails = Customer.objects.filter(
                created_at__gte=week_ago
            ).values_list('email_primary', flat=True)[:50]
            
            for email in recent_customer_emails:
                if email:
                    # Pre-cache search results for recent customer emails
                    cache_key = f"customer_search_email_{email}"
                    search_results = list(Customer.objects.filter(
                        email_primary__iexact=email
                    ).only('id', 'first_name', 'last_name', 'email_primary').values())
                    cache.set(cache_key, search_results, settings.CACHE_TTL['customer_search'])
            
            # Cache API endpoint responses for common queries
            if verbose:
                self.stdout.write('Caching common API responses...')
            
            # Cache customer list (first page)
            customers_page_1 = list(Customer.objects.select_related().only(
                'id', 'first_name', 'last_name', 'email_primary', 'customer_type', 'status'
            ).order_by('-created_at')[:20].values())
            cache.set('api_customers_page_1', customers_page_1, settings.CACHE_TTL['api_responses'])
            
            self.stdout.write(
                self.style.SUCCESS('Cache warming completed successfully!')
            )
            
            # Show cache statistics if verbose
            if verbose:
                cache_stats = {
                    'customer_stats': bool(cache.get('customer_stats_total')),
                    'country_codes': bool(cache.get('country_codes_list')),
                    'recent_customers': bool(cache.get('recent_customers_list')),
                    'active_courses': bool(cache.get('active_courses_list')),
                    'enrollment_stats': bool(cache.get('enrollment_stats')),
                    'customer_types': bool(cache.get('customer_type_distribution')),
                    'api_responses': bool(cache.get('api_customers_page_1')),
                }
                
                self.stdout.write('\nCache Status:')
                for key, cached in cache_stats.items():
                    status = self.style.SUCCESS('✓ Cached') if cached else self.style.ERROR('✗ Missing')
                    self.stdout.write(f'  {key}: {status}')
            
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            self.stdout.write(
                self.style.ERROR(f'Cache warming failed: {e}')
            )
            raise