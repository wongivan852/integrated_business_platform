# management/commands/create_default_templates.py
from django.core.management.base import BaseCommand
from crm.models import EmailTemplate

class Command(BaseCommand):
    help = 'Create default email templates'
    
    def handle(self, *args, **options):
        templates = [
            {
                'name': 'Welcome Email',
                'template_type': 'welcome',
                'subject': 'Welcome to {{institute_name}}!',
                'content_text': '''Dear {{first_name}},

Welcome to our learning community! We're excited to have you join us at {{institute_name}}.

You can explore our courses and upcoming conferences through our platform. If you have any questions, feel free to reach out to us at {{institute_email}} or call us at {{institute_phone}}.

We look forward to supporting your learning journey!

Best regards,
{{institute_name}} Team''',
                'content_html': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c5aa0;">Welcome to {{institute_name}}!</h2>
        
        <p>Dear {{first_name}},</p>
        
        <p>Welcome to our learning community! We're excited to have you join us at <strong>{{institute_name}}</strong>.</p>
        
        <p>You can explore our courses and upcoming conferences through our platform. If you have any questions, feel free to reach out to us at <a href="mailto:{{institute_email}}">{{institute_email}}</a> or call us at {{institute_phone}}.</p>
        
        <p>We look forward to supporting your learning journey!</p>
        
        <p>Best regards,<br>
        <strong>{{institute_name}} Team</strong></p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="font-size: 12px; color: #666;">
            This email was sent to {{email_primary}}. 
            If you no longer wish to receive these emails, you can unsubscribe.
        </p>
    </div>
</body>
</html>''',
                'available_variables': '{"first_name": "Customer first name", "institute_name": "Institute name", "institute_email": "Institute email", "institute_phone": "Institute phone", "email_primary": "Customer email"}'
            },
            {
                'name': 'Course Reminder',
                'template_type': 'course_reminder',
                'subject': 'Reminder: {{course_title}} starts soon!',
                'content_text': '''Dear {{first_name}},

This is a reminder that your course "{{course_title}}" is starting soon.

Course Details:
- Start Date: {{course_start_date}}
- Duration: {{course_duration}} hours

Please ensure you're prepared for the session. If you have any questions, don't hesitate to contact us.

Best regards,
{{institute_name}} Team''',
                'content_html': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c5aa0;">Course Reminder</h2>
        
        <p>Dear {{first_name}},</p>
        
        <p>This is a reminder that your course <strong>"{{course_title}}"</strong> is starting soon.</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #2c5aa0;">Course Details:</h3>
            <ul style="margin: 0;">
                <li><strong>Start Date:</strong> {{course_start_date}}</li>
                <li><strong>Duration:</strong> {{course_duration}} hours</li>
            </ul>
        </div>
        
        <p>Please ensure you're prepared for the session. If you have any questions, don't hesitate to contact us.</p>
        
        <p>Best regards,<br>
        <strong>{{institute_name}} Team</strong></p>
    </div>
</body>
</html>''',
                'available_variables': '{"first_name": "Customer first name", "course_title": "Course title", "course_start_date": "Course start date", "course_duration": "Course duration in hours", "institute_name": "Institute name"}'
            },
            {
                'name': 'Newsletter Template',
                'template_type': 'newsletter',
                'subject': '{{institute_name}} Newsletter - {{current_date}}',
                'content_text': '''Dear {{first_name}},

Welcome to our latest newsletter!

[Newsletter content goes here - customize this template with your actual newsletter content]

Featured this month:
- New courses and programs
- Upcoming events and conferences
- Student success stories

Stay connected with us and continue your learning journey!

Best regards,
{{institute_name}} Team

---
You're receiving this because you subscribed to our newsletter. 
Unsubscribe if you no longer wish to receive these updates.''',
                'content_html': '''<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <header style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #2c5aa0; margin: 0;">{{institute_name}} Newsletter</h1>
            <p style="color: #666; margin: 5px 0;">{{current_date}}</p>
        </header>
        
        <p>Dear {{first_name}},</p>
        
        <p>Welcome to our latest newsletter!</p>
        
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <p><em>[Newsletter content goes here - customize this template with your actual newsletter content]</em></p>
            
            <h3 style="color: #2c5aa0;">Featured this month:</h3>
            <ul>
                <li>New courses and programs</li>
                <li>Upcoming events and conferences</li>
                <li>Student success stories</li>
            </ul>
        </div>
        
        <p>Stay connected with us and continue your learning journey!</p>
        
        <p>Best regards,<br>
        <strong>{{institute_name}} Team</strong></p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="font-size: 12px; color: #666; text-align: center;">
            You're receiving this because you subscribed to our newsletter.<br>
            <a href="#" style="color: #666;">Unsubscribe</a> if you no longer wish to receive these updates.
        </p>
    </div>
</body>
</html>''',
                'available_variables': '{"first_name": "Customer first name", "institute_name": "Institute name", "current_date": "Current date", "email_primary": "Customer email"}'
            }
        ]
        
        created_count = 0
        for template_data in templates:
            template, created = EmailTemplate.objects.get_or_create(
                name=template_data['name'],
                template_type=template_data['template_type'],
                defaults={
                    'subject': template_data['subject'],
                    'content_text': template_data['content_text'],
                    'content_html': template_data['content_html'],
                    'available_variables': template_data['available_variables'],
                    'status': 'active',
                    'created_by': 'System Default'
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Template already exists: {template.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} default templates')
        )