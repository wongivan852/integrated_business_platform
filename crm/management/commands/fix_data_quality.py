"""
Django management command to fix data quality issues in the CRM system
Usage: python manage.py fix_data_quality
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from crm.data_quality import DataQualityService
import logging

logger = logging.getLogger('crm.management')

class Command(BaseCommand):
    help = 'Fix data quality issues in the CRM system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--report-only',
            action='store_true',
            help='Only generate a report without making changes',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )
        parser.add_argument(
            '--fix-emails',
            action='store_true',
            help='Fix email format issues',
        )
        parser.add_argument(
            '--detect-countries',
            action='store_true',
            help='Detect missing countries from email domains',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Starting data quality check at {timezone.now()}')
        )
        
        service = DataQualityService()
        
        # Generate quality report first
        self.stdout.write('Generating data quality report...')
        report = service.get_data_quality_report()
        
        self.display_report(report)
        
        if options['report_only']:
            self.stdout.write(
                self.style.SUCCESS('Report-only mode: No changes made.')
            )
            return
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE: No actual changes will be made.')
            )
            # TODO: Implement dry-run logic
            return
        
        # Run fixes
        if report['issues']['invalid_emails'] > 0 or report['issues']['missing_countries'] > 0:
            self.stdout.write('Running data quality fixes...')
            
            results = service.fix_failed_records()
            
            self.display_fix_results(results)
        else:
            self.stdout.write(
                self.style.SUCCESS('No data quality issues found. System is healthy!')
            )
    
    def display_report(self, report):
        """Display the data quality report"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('DATA QUALITY REPORT'))
        self.stdout.write('='*60)
        
        self.stdout.write(f'Total Customers: {report["total_customers"]}')
        self.stdout.write(f'Report Time: {report["timestamp"]}')
        
        self.stdout.write('\n' + '-'*40)
        self.stdout.write(self.style.WARNING('ISSUES FOUND:'))
        self.stdout.write('-'*40)
        
        issues = report['issues']
        for issue, count in issues.items():
            issue_name = issue.replace('_', ' ').title()
            if count > 0:
                self.stdout.write(
                    self.style.ERROR(f'{issue_name}: {count}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'{issue_name}: {count}')
                )
        
        self.stdout.write('\n' + '-'*40)
        self.stdout.write(self.style.SUCCESS('QUALITY SCORES:'))
        self.stdout.write('-'*40)
        
        scores = report['quality_scores']
        for metric, score in scores.items():
            metric_name = metric.replace('_', ' ').title()
            if score >= 90:
                style = self.style.SUCCESS
            elif score >= 70:
                style = self.style.WARNING
            else:
                style = self.style.ERROR
            
            self.stdout.write(style(f'{metric_name}: {score}%'))
        
        self.stdout.write('='*60 + '\n')
    
    def display_fix_results(self, results):
        """Display the results of data quality fixes"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('DATA QUALITY FIX RESULTS'))
        self.stdout.write('='*60)
        
        self.stdout.write(f'Processed: {results["processed"]} customers')
        
        if results['fixed'] > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Fixed: {results["fixed"]} customers')
            )
        
        if results['still_invalid'] > 0:
            self.stdout.write(
                self.style.ERROR(f'Still Invalid: {results["still_invalid"]} customers')
            )
        
        if results['errors']:
            self.stdout.write('\n' + self.style.ERROR('ERRORS:'))
            for error in results['errors'][:10]:  # Show first 10 errors
                self.stdout.write(self.style.ERROR(f'  - {error}'))
            
            if len(results['errors']) > 10:
                self.stdout.write(
                    self.style.ERROR(f'  ... and {len(results["errors"]) - 10} more errors')
                )
        
        self.stdout.write('='*60 + '\n')
        
        if results['fixed'] > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Data quality improvements completed! '
                    f'{results["fixed"]} customers were fixed.'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('No customers could be automatically fixed.')
            )