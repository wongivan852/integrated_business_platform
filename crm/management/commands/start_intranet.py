from django.core.management.base import BaseCommand
from django.core.management.commands.runserver import Command as RunServerCommand
import socket


class Command(BaseCommand):
    help = 'Start CRM server on port 8000 for intranet access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            default='0.0.0.0',
            help='IP address to bind to (default: 0.0.0.0 for intranet access)'
        )
        parser.add_argument(
            '--port',
            default='8000',
            help='Port to run on (default: 8000)'
        )

    def handle(self, *args, **options):
        host = options['host']
        port = options['port']
        
        # Get local IP for display
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "your-ip"
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🚀 Starting CRM Server for Intranet Access\n'
                f'📍 Local Access: http://localhost:{port}\n'
                f'🌐 Intranet Access: http://{local_ip}:{port}\n'
                f'🔒 Admin Panel: http://{local_ip}:{port}/admin\n'
                f'📊 API Endpoint: http://{local_ip}:{port}/api/v1\n'
                f'{'='*50}\n'
            )
        )
        
        # Use Django's built-in runserver command
        runserver = RunServerCommand()
        runserver.stdout = self.stdout
        runserver.stderr = self.stderr
        runserver.handle(f'{host}:{port}', **{
            'verbosity': options.get('verbosity', 1),
            'settings': None,
            'pythonpath': None,
            'traceback': options.get('traceback', False),
            'no_color': options.get('no_color', False),
            'force_color': options.get('force_color', False),
            'use_reloader': True,
            'use_threading': True,
            'use_static_handler': True,
            'insecure': False,
            'skip_checks': False
        })