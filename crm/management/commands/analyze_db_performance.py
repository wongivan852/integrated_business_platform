"""
Django management command to analyze database performance and suggest optimizations
Usage: python manage.py analyze_db_performance
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from django.conf import settings
import time

class Command(BaseCommand):
    help = 'Analyze database performance and suggest optimizations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--slow-queries',
            action='store_true',
            help='Show slow query analysis',
        )
        parser.add_argument(
            '--index-usage',
            action='store_true',
            help='Show index usage statistics',
        )
        parser.add_argument(
            '--table-stats',
            action='store_true',
            help='Show table size and statistics',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all analyses',
        )
    
    def handle(self, *args, **options):
        if not any([options['slow_queries'], options['index_usage'], options['table_stats'], options['all']]):
            options['all'] = True
        
        self.stdout.write(
            self.style.SUCCESS(f'Database Performance Analysis - {timezone.now()}')
        )
        self.stdout.write('='*80)
        
        if options['all'] or options['table_stats']:
            self.analyze_table_stats()
        
        if options['all'] or options['index_usage']:
            self.analyze_index_usage()
        
        if options['all'] or options['slow_queries']:
            self.analyze_slow_queries()
        
        self.provide_recommendations()
    
    def analyze_table_stats(self):
        """Analyze table sizes and statistics"""
        self.stdout.write('\n' + self.style.WARNING('TABLE STATISTICS'))
        self.stdout.write('-'*50)
        
        try:
            with connection.cursor() as cursor:
                # PostgreSQL specific queries
                if 'postgresql' in settings.DATABASES['default']['ENGINE']:
                    cursor.execute("""
                        SELECT 
                            schemaname,
                            tablename,
                            attname as column_name,
                            n_distinct,
                            correlation
                        FROM pg_stats 
                        WHERE schemaname = 'public' 
                        AND tablename LIKE 'crm_%'
                        ORDER BY tablename, attname;
                    """)
                    
                    current_table = None
                    for row in cursor.fetchall():
                        schema, table, column, n_distinct, correlation = row
                        if table != current_table:
                            self.stdout.write(f'\n{table.upper()}:')
                            current_table = table
                        
                        distinct_info = f"Distinct: {n_distinct}" if n_distinct else "Distinct: Unknown"
                        corr_info = f"Correlation: {correlation:.3f}" if correlation else "Correlation: N/A"
                        self.stdout.write(f'  {column}: {distinct_info}, {corr_info}')
                    
                    # Table sizes
                    cursor.execute("""
                        SELECT 
                            tablename,
                            pg_size_pretty(pg_total_relation_size('crm_'||tablename)) as size,
                            pg_total_relation_size('crm_'||tablename) as size_bytes
                        FROM pg_tables 
                        WHERE schemaname = 'public' 
                        AND tablename LIKE 'crm_%'
                        ORDER BY pg_total_relation_size('crm_'||tablename) DESC;
                    """)
                    
                    self.stdout.write('\nTABLE SIZES:')
                    for row in cursor.fetchall():
                        table, size, size_bytes = row
                        self.stdout.write(f'  crm_{table}: {size}')
                else:
                    self.stdout.write('Table statistics analysis is optimized for PostgreSQL')
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error analyzing table stats: {str(e)}')
            )
    
    def analyze_index_usage(self):
        """Analyze index usage and effectiveness"""
        self.stdout.write('\n' + self.style.WARNING('INDEX USAGE ANALYSIS'))
        self.stdout.write('-'*50)
        
        try:
            with connection.cursor() as cursor:
                if 'postgresql' in settings.DATABASES['default']['ENGINE']:
                    # Index usage statistics
                    cursor.execute("""
                        SELECT
                            schemaname,
                            tablename,
                            indexname,
                            idx_tup_read as reads,
                            idx_tup_fetch as fetches,
                            idx_scan as scans
                        FROM pg_stat_user_indexes
                        WHERE schemaname = 'public'
                        AND tablename LIKE 'crm_%'
                        ORDER BY idx_scan DESC;
                    """)
                    
                    self.stdout.write('INDEX USAGE (by scan frequency):')
                    for row in cursor.fetchall():
                        schema, table, index, reads, fetches, scans = row
                        usage_indicator = "🔥" if scans > 1000 else "⚠️" if scans > 100 else "🔍"
                        self.stdout.write(f'  {usage_indicator} {index}: {scans} scans, {reads} reads')
                    
                    # Unused indexes
                    cursor.execute("""
                        SELECT
                            schemaname,
                            tablename,
                            indexname
                        FROM pg_stat_user_indexes
                        WHERE schemaname = 'public'
                        AND tablename LIKE 'crm_%'
                        AND idx_scan = 0
                        ORDER BY tablename, indexname;
                    """)
                    
                    unused_indexes = cursor.fetchall()
                    if unused_indexes:
                        self.stdout.write('\nUNUSED INDEXES (consider removing):')
                        for row in unused_indexes:
                            schema, table, index = row
                            self.stdout.write(
                                self.style.ERROR(f'  ❌ {index} on {table}')
                            )
                    
                    # Index sizes
                    cursor.execute("""
                        SELECT
                            indexname,
                            pg_size_pretty(pg_relation_size(indexrelid)) as size
                        FROM pg_stat_user_indexes
                        WHERE schemaname = 'public'
                        AND tablename LIKE 'crm_%'
                        ORDER BY pg_relation_size(indexrelid) DESC
                        LIMIT 10;
                    """)
                    
                    self.stdout.write('\nLARGEST INDEXES:')
                    for row in cursor.fetchall():
                        index, size = row
                        self.stdout.write(f'  {index}: {size}')
                else:
                    self.stdout.write('Index analysis is optimized for PostgreSQL')
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error analyzing indexes: {str(e)}')
            )
    
    def analyze_slow_queries(self):
        """Analyze query performance"""
        self.stdout.write('\n' + self.style.WARNING('QUERY PERFORMANCE TEST'))
        self.stdout.write('-'*50)
        
        # Test common queries
        test_queries = [
            {
                'name': 'Customer List Query',
                'sql': 'SELECT id, first_name, last_name, email_primary, status FROM crm_customer ORDER BY created_at DESC LIMIT 20'
            },
            {
                'name': 'Customer Search by Email',
                'sql': "SELECT id, first_name, last_name FROM crm_customer WHERE email_primary ILIKE '%@gmail.com%' LIMIT 10"
            },
            {
                'name': 'Customer Count by Type',
                'sql': 'SELECT customer_type, COUNT(*) FROM crm_customer GROUP BY customer_type'
            },
            {
                'name': 'Recent Communications',
                'sql': "SELECT customer_id, channel, sent_at FROM crm_communicationlog WHERE sent_at >= CURRENT_DATE - INTERVAL '7 days' ORDER BY sent_at DESC LIMIT 20"
            },
            {
                'name': 'Active Enrollments',
                'sql': "SELECT customer_id, course_id, status FROM crm_enrollment WHERE status = 'registered' LIMIT 20"
            }
        ]
        
        with connection.cursor() as cursor:
            for query in test_queries:
                start_time = time.time()
                try:
                    cursor.execute(query['sql'])
                    results = cursor.fetchall()
                    duration = (time.time() - start_time) * 1000  # milliseconds
                    
                    status_icon = "🚀" if duration < 50 else "⚠️" if duration < 200 else "🐌"
                    status_color = self.style.SUCCESS if duration < 50 else self.style.WARNING if duration < 200 else self.style.ERROR
                    
                    self.stdout.write(
                        f'{status_icon} {query["name"]}: ' + 
                        status_color(f'{duration:.2f}ms') + 
                        f' ({len(results)} rows)'
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {query["name"]}: Error - {str(e)}')
                    )
    
    def provide_recommendations(self):
        """Provide performance recommendations"""
        self.stdout.write('\n' + self.style.SUCCESS('PERFORMANCE RECOMMENDATIONS'))
        self.stdout.write('='*50)
        
        recommendations = [
            "✅ Monitor slow queries regularly (> 200ms should be investigated)",
            "✅ Consider VACUUM ANALYZE on PostgreSQL weekly for table statistics",
            "✅ Review unused indexes periodically and remove if not needed",
            "✅ Use connection pooling in production (already configured)",
            "✅ Enable query logging for queries > 1000ms in production",
            "✅ Consider read replicas if read queries dominate",
            "✅ Monitor database connection counts and adjust pool size",
            "✅ Use EXPLAIN ANALYZE for slow queries to understand execution plans",
            "✅ Consider partitioning large tables (> 1M rows) by date",
            "✅ Regular backup and restore testing for disaster recovery"
        ]
        
        for rec in recommendations:
            self.stdout.write(rec)
        
        self.stdout.write('\n' + self.style.SUCCESS('MAINTENANCE COMMANDS:'))
        self.stdout.write('='*30)
        maintenance_commands = [
            "# PostgreSQL maintenance (run as needed):",
            "VACUUM ANALYZE;  # Update table statistics",
            "REINDEX DATABASE your_db_name;  # Rebuild indexes if needed",
            "",
            "# Django ORM optimization:",
            "# Use select_related() for foreign keys",
            "# Use prefetch_related() for many-to-many and reverse foreign keys",
            "# Use only() and defer() to limit fields",
            "# Use iterator() for large querysets",
            "",
            "# Monitoring queries:",
            "# Enable pg_stat_statements extension",
            "# Monitor with: SELECT * FROM pg_stat_statements ORDER BY total_time DESC;"
        ]
        
        for cmd in maintenance_commands:
            if cmd.startswith('#'):
                self.stdout.write(self.style.WARNING(cmd))
            else:
                self.stdout.write(cmd)
        
        self.stdout.write('\n' + '='*80)