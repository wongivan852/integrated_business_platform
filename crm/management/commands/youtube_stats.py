from django.core.management.base import BaseCommand
from crm.youtube_service import youtube_service
from crm.models import YouTubeMessage, Customer


class Command(BaseCommand):
    help = 'Show YouTube messaging statistics and monitor feedback'

    def add_arguments(self, parser):
        parser.add_argument('--handle', type=str, help='Show stats for specific YouTube handle')
        parser.add_argument('--retry-failed', action='store_true', help='Retry failed messages')
        parser.add_argument('--recent', type=int, default=10, help='Show N recent messages')

    def handle(self, *args, **options):
        handle = options.get('handle')
        retry_failed = options.get('retry_failed')
        recent_count = options.get('recent')

        if retry_failed:
            self.stdout.write(
                self.style.HTTP_INFO('🔄 Retrying failed messages...')
            )
            results = youtube_service.retry_failed_messages()
            self.stdout.write(f'   Attempted: {results["attempted"]}')
            self.stdout.write(
                self.style.SUCCESS(f'   ✅ Succeeded: {results["succeeded"]}')
            )
            self.stdout.write(
                self.style.ERROR(f'   ❌ Failed: {results["failed"]}')
            )
            self.stdout.write('')

        # Show statistics
        stats = youtube_service.get_message_statistics(handle)
        
        title = f'📊 YouTube Messaging Statistics'
        if handle:
            title += f' for @{handle.lstrip("@")}'
        
        self.stdout.write(self.style.HTTP_INFO(title))
        self.stdout.write(f'   Total Messages: {stats["total_messages"]}')
        self.stdout.write(
            self.style.SUCCESS(f'   ✅ Sent: {stats["sent_messages"]}')
        )
        self.stdout.write(f'   ⏳ Pending: {stats["pending_messages"]}')
        self.stdout.write(
            self.style.ERROR(f'   ❌ Failed: {stats["failed_messages"]}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   💬 Replied: {stats["replied_messages"]}')
        )
        self.stdout.write(f'   📈 Success Rate: {stats["success_rate"]:.1f}%')
        self.stdout.write('')

        # Show recent messages
        queryset = YouTubeMessage.objects.all()
        if handle:
            queryset = queryset.filter(target_youtube_handle__iexact=handle.lstrip('@'))
        
        recent_messages = queryset.order_by('-created_at')[:recent_count]
        
        if recent_messages:
            self.stdout.write(
                self.style.HTTP_INFO(f'📋 Recent Messages (Last {len(recent_messages)})')
            )
            
            for msg in recent_messages:
                status_icon = {
                    'draft': '✏️',
                    'pending': '⏳',
                    'sent': '✅',
                    'delivered': '📫',
                    'read': '👁️',
                    'replied': '💬',
                    'failed': '❌',
                    'bounced': '↩️'
                }.get(msg.status, '❓')
                
                priority_text = ['', 'HIGH', 'MED', 'LOW'][msg.priority]
                
                self.stdout.write(
                    f'   {status_icon} @{msg.target_youtube_handle}: {msg.subject}'
                )
                self.stdout.write(
                    f'      {msg.get_message_type_display()} | {priority_text} | {msg.created_at.strftime("%Y-%m-%d %H:%M")}'
                )
                
                if msg.response_received:
                    self.stdout.write(
                        self.style.SUCCESS(f'      💬 Response: {msg.response_content[:100]}...')
                    )
                
                if msg.status == 'failed' and msg.error_message:
                    self.stdout.write(
                        self.style.ERROR(f'      ❌ Error: {msg.error_message[:100]}...')
                    )
                
                self.stdout.write('')

        # Show customers with YouTube handles
        youtube_customers = Customer.objects.filter(
            youtube_handle__isnull=False
        ).exclude(youtube_handle='')
        
        if youtube_customers.exists():
            self.stdout.write(
                self.style.HTTP_INFO(f'👥 YouTube Customers ({youtube_customers.count()})')
            )
            
            for customer in youtube_customers.order_by('-created_at')[:10]:
                message_count = customer.youtube_messages.count()
                latest_message = customer.youtube_messages.order_by('-created_at').first()
                
                self.stdout.write(
                    f'   @{customer.youtube_handle}: {customer.first_name} {customer.last_name}'
                )
                self.stdout.write(
                    f'      Messages: {message_count} | Created: {customer.created_at.strftime("%Y-%m-%d")}'
                )
                
                if latest_message:
                    self.stdout.write(
                        f'      Latest: {latest_message.subject} ({latest_message.status})'
                    )
                
                self.stdout.write('')