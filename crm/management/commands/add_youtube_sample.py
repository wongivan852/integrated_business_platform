# management/commands/add_youtube_sample.py
from django.core.management.base import BaseCommand
from crm.models import Customer

class Command(BaseCommand):
    help = 'Add sample YouTube creators with handles and minimal data'

    def handle(self, *args, **options):
        youtube_creators = [
            {
                'first_name': 'TechReview',
                'last_name': 'Channel',
                'youtube_handle': 'TechReviewOfficial',
                'customer_type': 'youtuber',
                'company_primary': 'TechReview Media'
            },
            {
                'first_name': 'Sarah',
                'last_name': 'Learns',
                'youtube_handle': 'LearnWithSarahDaily',
                'customer_type': 'youtuber',
                'company_primary': 'Learning Content Studio'
            },
            {
                'first_name': 'Gaming',
                'last_name': 'Pro',
                'youtube_handle': 'GamingProTips',
                'customer_type': 'youtuber',
                'company_primary': 'Gaming Pro Channel'
            },
            {
                'first_name': 'Emma',
                'last_name': 'Cooks',
                'youtube_handle': 'EmmaCooksDaily',
                'customer_type': 'youtuber',
                'company_primary': 'Cooking Channel'
            },
            {
                'first_name': 'Fitness',
                'last_name': 'Journey',
                'youtube_handle': 'FitnessJourney2024',
                'customer_type': 'youtuber',
                'company_primary': 'Fitness Journey'
            },
            {
                'first_name': 'Travel',
                'last_name': 'Vlog',
                'youtube_handle': 'TravelVlogWorld',
                'customer_type': 'youtuber',
                'company_primary': 'Travel Vlog'
            },
            {
                'first_name': 'DIY',
                'last_name': 'Master',
                'youtube_handle': 'DIYMasterCraft',
                'customer_type': 'youtuber',
                'company_primary': 'DIY Master Studio'
            },
            {
                'first_name': 'Music',
                'last_name': 'Studio',
                'youtube_handle': 'MusicStudioBeats',
                'customer_type': 'youtuber',
                'company_primary': 'Music Studio'
            },
            {
                'first_name': 'Art',
                'last_name': 'Creator',
                'youtube_handle': 'ArtCreatorDaily',
                'customer_type': 'youtuber',
                'company_primary': 'Art Creator Studio'
            },
            {
                'first_name': 'Code',
                'last_name': 'Academy',
                'youtube_handle': 'CodeAcademyPro',
                'customer_type': 'youtuber',
                'company_primary': 'Code Academy'
            },
            {
                'first_name': 'Lifestyle',
                'last_name': 'Guru',
                'youtube_handle': 'LifestyleGuruTips',
                'customer_type': 'youtuber',
                'company_primary': 'Lifestyle Guru'
            }
        ]
        
        created_count = 0
        
        for creator_data in youtube_creators:
            # Check if YouTube creator already exists
            existing = Customer.objects.filter(
                youtube_handle=creator_data['youtube_handle']
            ).first()
            
            if existing:
                self.stdout.write(f'Skipped existing creator: @{creator_data["youtube_handle"]}')
                continue
            
            # Create full customer data
            customer_data = {
                'first_name': creator_data['first_name'],
                'last_name': creator_data['last_name'],
                'youtube_handle': creator_data['youtube_handle'],
                'youtube_channel_url': f"https://youtube.com/@{creator_data['youtube_handle']}",
                'customer_type': creator_data['customer_type'],
                'company_primary': creator_data['company_primary'],
                'position_primary': 'Content Creator',
                'status': 'prospect',
                'preferred_communication_method': 'whatsapp',  # No email for YouTube-only creators
                'referral_source': 'youtube_discovery',
                'interests': 'Content Creation, Video Production, YouTube Marketing',
                'internal_notes': 'YouTube creator with handle and name only - no email contact',
            }
            
            try:
                customer = Customer(**customer_data)
                customer.full_clean()
                customer.save()
                
                created_count += 1
                self.stdout.write(f'Created YouTube creator: @{customer.youtube_handle} - {customer.first_name} {customer.last_name}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating @{creator_data["youtube_handle"]}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Added {created_count} YouTube creators with handles only')
        )
