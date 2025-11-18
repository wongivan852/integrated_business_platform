# optimize_db.py - Database optimization management command
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger('crm.performance')

class Command(BaseCommand):
    help = 'Optimize database for UAT performance - analyze tables and suggest improvements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Run ANALYZE on all tables to update statistics',
        )
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='Run VACUUM on all tables (PostgreSQL only)',
        )
        parser.add_argument(
            '--show-queries',
            action='store_true',
            help='Show slow queries and optimization suggestions',
        )

    def handle(self, *args, **options):
        if 'postgresql' not in settings.DATABASES['default']['ENGINE']:
            self.stdout.write(
                self.style.WARNING('This command is optimized for PostgreSQL databases')
            )
            return

        with connection.cursor() as cursor:
            if options['analyze']:
                self.stdout.write('Running ANALYZE on all tables...')
                try:
                    cursor.execute('ANALYZE;')
                    self.stdout.write(
                        self.style.SUCCESS('Database analysis completed successfully')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Analysis failed: {e}')
                    )

            if options['vacuum']:
                self.stdout.write('Running VACUUM on all tables...')
                try:
                    # Note: VACUUM cannot run inside a transaction
                    cursor.execute('VACUUM;')
                    self.stdout.write(
                        self.style.SUCCESS('Database vacuum completed successfully')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Vacuum failed: {e}')
                    )

            if options['show_queries']:
                self.stdout.write('Analyzing query performance...')
                self._show_query_performance(cursor)
                self._show_index_usage(cursor)
                self._show_table_stats(cursor)

    def _show_query_performance(self, cursor):
        """Show slow queries and performance statistics"""
        try:
            # Check if pg_stat_statements extension is available
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
                );
            """)
            
            if cursor.fetchone()[0]:
                self.stdout.write('\n📊 Top 10 slowest queries:')
                cursor.execute("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows
                    FROM pg_stat_statements 
                    WHERE query LIKE '%crm_%'
                    ORDER BY mean_time DESC 
                    LIMIT 10;
                """)
                
                for row in cursor.fetchall():
                    query, calls, total_time, mean_time, rows = row
                    self.stdout.write(f'  • {query[:80]}...')
                    self.stdout.write(f'    Calls: {calls}, Mean time: {mean_time:.2f}ms')
            else:
                self.stdout.write(
                    self.style.WARNING('pg_stat_statements extension not installed')
                )
        except Exception as e:
            self.stdout.write(f'Query analysis failed: {e}')

    def _show_index_usage(self, cursor):
        """Show index usage statistics"""
        try:
            self.stdout.write('\n📈 Index usage statistics:')
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes 
                WHERE schemaname = 'public'
                AND tablename LIKE 'crm_%'
                ORDER BY idx_scan DESC;
            """)
            
            for row in cursor.fetchall():
                schema, table, index, scans, reads, fetches = row
                self.stdout.write(f'  • {table}.{index}: {scans} scans, {reads} reads')
                
        except Exception as e:
            self.stdout.write(f'Index analysis failed: {e}')

    def _show_table_stats(self, cursor):
        """Show table statistics"""
        try:
            self.stdout.write('\n📋 Table statistics:')
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    last_vacuum,
                    last_analyze
                FROM pg_stat_user_tables 
                WHERE schemaname = 'public'
                AND tablename LIKE 'crm_%'
                ORDER BY n_live_tup DESC;
            """)
            
            for row in cursor.fetchall():
                (schema, table, inserts, updates, deletes, 
                 live_tuples, dead_tuples, last_vacuum, last_analyze) = row
                
                self.stdout.write(f'  • {table}:')
                self.stdout.write(f'    Live tuples: {live_tuples}, Dead tuples: {dead_tuples}')
                self.stdout.write(f'    Operations: {inserts}I/{updates}U/{deletes}D')
                
                if dead_tuples > live_tuples * 0.1:
                    self.stdout.write(
                        self.style.WARNING(f'    ⚠️  High dead tuple ratio, consider VACUUM')
                    )
                
        except Exception as e:
            self.stdout.write(f'Table analysis failed: {e}')

        # Show optimization recommendations
        self.stdout.write('\n🔧 Optimization Recommendations:')
        self._show_recommendations()

    def _show_recommendations(self):
        """Show database optimization recommendations"""
        recommendations = [
            "Run 'python manage.py migrate' to ensure all indexes are created",
            "Consider running VACUUM ANALYZE weekly for optimal performance",
            "Monitor slow queries and add indexes for frequently filtered fields",
            "Use connection pooling (pgbouncer) for production deployments",
            "Consider partitioning large tables (>1M rows) by date",
            "Enable query caching for frequently accessed data",
        ]
        
        for i, rec in enumerate(recommendations, 1):
            self.stdout.write(f'  {i}. {rec}')
        
        self.stdout.write('\n💡 To apply database optimizations:')
        self.stdout.write('  python manage.py optimize_db --analyze --vacuum')
        self.stdout.write('  python manage.py warm_cache --clear-first --verbose')