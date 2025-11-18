from django.core.management.base import BaseCommand
from crm.youtube_service import youtube_service
from crm.models import YouTubeMessage


class Command(BaseCommand):
    help = 'Send a message to a YouTube creator via their handle'

    def add_arguments(self, parser):
        parser.add_argument('youtube_handle', type=str, help='YouTube handle (with or without @)')
        parser.add_argument('subject', type=str, help='Message subject')
        parser.add_argument('content', type=str, help='Message content')
        
        parser.add_argument('--type', type=str, default='direct_message',
                          choices=['direct_message', 'comment', 'community_post', 'collaboration', 'business'],
                          help='Type of message')
        parser.add_argument('--priority', type=int, default=3, choices=[1, 2, 3],
                          help='Message priority (1=High, 2=Medium, 3=Low)')
        parser.add_argument('--video-url', type=str, help='Video URL for comments')

    def handle(self, *args, **options):
        youtube_handle = options['youtube_handle']
        subject = options['subject']
        content = options['content']
        message_type = options['type']
        priority = options['priority']
        video_url = options.get('video_url')

        self.stdout.write(
            self.style.HTTP_INFO(f'📤 Sending {message_type} to @{youtube_handle.lstrip("@")}')
        )
        self.stdout.write(f'   Subject: {subject}')
        self.stdout.write(f'   Priority: {["", "High", "Medium", "Low"][priority]}')
        if video_url:
            self.stdout.write(f'   Video URL: {video_url}')

        try:
            success, message, youtube_message = youtube_service.send_message_to_handle(
                youtube_handle=youtube_handle,
                subject=subject,
                content=content,
                message_type=message_type,
                priority=priority,
                video_url=video_url
            )

            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {message}')
                )
                self.stdout.write(f'   Message ID: {youtube_message.id}')
                self.stdout.write(f'   Customer: {youtube_message.customer.first_name} {youtube_message.customer.last_name}')
                self.stdout.write(f'   Target URL: {youtube_message.get_target_url()}')
                self.stdout.write(f'   Status: {youtube_message.get_status_display()}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ {message}')
                )
                if youtube_message:
                    self.stdout.write(f'   Error details: {youtube_message.error_message}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to send message: {str(e)}')
            )