"""
YouTube Messaging Service
Handles sending messages to YouTube creators via their handles
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.conf import settings
from .models import Customer, YouTubeMessage, CommunicationLog

logger = logging.getLogger(__name__)


class YouTubeMessagingService:
    """Service for sending messages to YouTube creators"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'YOUTUBE_API_KEY', None)
        self.sender_email = getattr(settings, 'YOUTUBE_SENDER_EMAIL', 'contact@yourcompany.com')
        self.sender_name = getattr(settings, 'YOUTUBE_SENDER_NAME', 'Your Company')
        
    def send_message_to_handle(
        self, 
        youtube_handle: str, 
        subject: str, 
        content: str,
        message_type: str = 'direct_message',
        priority: int = 3,
        video_url: str = None
    ) -> Tuple[bool, str, Optional[YouTubeMessage]]:
        """
        Send a message to a YouTube creator via their handle
        
        Args:
            youtube_handle: YouTube handle (without @)
            subject: Message subject
            content: Message content
            message_type: Type of message (direct_message, comment, etc.)
            priority: Message priority (1=High, 2=Medium, 3=Low)
            video_url: Specific video URL if commenting
            
        Returns:
            Tuple of (success, message, youtube_message_object)
        """
        try:
            # Clean the handle
            clean_handle = youtube_handle.lstrip('@')
            
            # Find or create customer based on YouTube handle
            customer = self._get_or_create_customer(clean_handle)
            
            # Create YouTubeMessage record
            youtube_message = YouTubeMessage.objects.create(
                customer=customer,
                message_type=message_type,
                subject=subject,
                content=content,
                target_youtube_handle=clean_handle,
                target_video_url=video_url or '',
                priority=priority,
                status='pending'
            )
            
            # Attempt to send the message
            success, result_message = self._send_message(youtube_message)
            
            if success:
                youtube_message.mark_as_sent(
                    external_id=f"yt_{int(time.time())}",
                    sent_by=self.sender_name
                )
                
                # Also log in CommunicationLog
                CommunicationLog.objects.create(
                    customer=customer,
                    channel='youtube',
                    subject=subject,
                    content=content,
                    is_outbound=True,
                    external_message_id=youtube_message.external_message_id
                )
                
                return True, f"Message sent successfully to @{clean_handle}", youtube_message
            else:
                youtube_message.mark_as_failed(result_message)
                return False, result_message, youtube_message
                
        except Exception as e:
            logger.error(f"Error sending YouTube message to @{youtube_handle}: {str(e)}")
            return False, f"Error: {str(e)}", None
    
    def _get_or_create_customer(self, youtube_handle: str) -> Customer:
        """Get or create customer based on YouTube handle"""
        try:
            # Try to find existing customer
            customer = Customer.objects.get(youtube_handle__iexact=youtube_handle)
            return customer
        except Customer.DoesNotExist:
            # Create new YouTuber customer
            customer = Customer(
                customer_type='youtuber',
                youtube_handle=youtube_handle
            )
            # The clean() method will auto-generate required fields
            customer.full_clean()
            customer.save()
            return customer
    
    def _send_message(self, youtube_message: YouTubeMessage) -> Tuple[bool, str]:
        """
        Actual message sending logic
        
        Note: This is a placeholder implementation. In production, you would:
        1. Use YouTube Data API to send comments
        2. Use email to business email if available
        3. Use third-party services like Mailchimp, SendGrid
        4. Use social media automation tools
        """
        
        # Simulate different messaging strategies
        if youtube_message.message_type == 'comment' and youtube_message.target_video_url:
            return self._send_video_comment(youtube_message)
        elif youtube_message.message_type == 'direct_message':
            return self._send_direct_message(youtube_message)
        elif youtube_message.message_type == 'business':
            return self._send_business_inquiry(youtube_message)
        else:
            return self._send_generic_message(youtube_message)
    
    def _send_video_comment(self, youtube_message: YouTubeMessage) -> Tuple[bool, str]:
        """Send a comment on a specific video"""
        # Placeholder for YouTube API comment posting
        logger.info(f"Sending comment to video: {youtube_message.target_video_url}")
        
        # In production, implement YouTube Data API comment posting:
        # youtube_service.comments().insert(
        #     part="snippet",
        #     body={
        #         "snippet": {
        #             "videoId": video_id,
        #             "topLevelComment": {
        #                 "snippet": {
        #                     "textOriginal": youtube_message.content
        #                 }
        #             }
        #         }
        #     }
        # )
        
        return True, "Comment posted successfully (simulated)"
    
    def _send_direct_message(self, youtube_message: YouTubeMessage) -> Tuple[bool, str]:
        """Send a direct message to YouTube creator"""
        # Placeholder for direct messaging
        logger.info(f"Sending direct message to @{youtube_message.target_youtube_handle}")
        
        # In production, implement:
        # 1. Try to find creator's business email
        # 2. Use social media automation tools
        # 3. Use platform-specific messaging APIs
        
        return True, "Direct message sent successfully (simulated)"
    
    def _send_business_inquiry(self, youtube_message: YouTubeMessage) -> Tuple[bool, str]:
        """Send a business inquiry"""
        # Placeholder for business inquiry
        logger.info(f"Sending business inquiry to @{youtube_message.target_youtube_handle}")
        
        # In production:
        # 1. Look for business contact info in channel about page
        # 2. Use professional networking platforms
        # 3. Send via email if available
        
        return True, "Business inquiry sent successfully (simulated)"
    
    def _send_generic_message(self, youtube_message: YouTubeMessage) -> Tuple[bool, str]:
        """Send a generic message"""
        logger.info(f"Sending generic message to @{youtube_message.target_youtube_handle}")
        return True, "Generic message sent successfully (simulated)"
    
    def get_message_statistics(self, youtube_handle: str = None) -> Dict:
        """Get messaging statistics"""
        queryset = YouTubeMessage.objects.all()
        
        if youtube_handle:
            queryset = queryset.filter(target_youtube_handle__iexact=youtube_handle.lstrip('@'))
        
        stats = {
            'total_messages': queryset.count(),
            'sent_messages': queryset.filter(status='sent').count(),
            'pending_messages': queryset.filter(status='pending').count(),
            'failed_messages': queryset.filter(status='failed').count(),
            'replied_messages': queryset.filter(status='replied').count(),
            'success_rate': 0.0
        }
        
        if stats['total_messages'] > 0:
            stats['success_rate'] = (stats['sent_messages'] / stats['total_messages']) * 100
        
        return stats
    
    def retry_failed_messages(self, max_retries: int = 3) -> Dict:
        """Retry failed messages that haven't exceeded max retries"""
        failed_messages = YouTubeMessage.objects.filter(
            status='failed',
            retry_count__lt=max_retries
        )
        
        results = {
            'attempted': 0,
            'succeeded': 0,
            'failed': 0
        }
        
        for message in failed_messages:
            results['attempted'] += 1
            success, result_msg = self._send_message(message)
            
            if success:
                message.mark_as_sent()
                results['succeeded'] += 1
            else:
                message.mark_as_failed(result_msg)
                results['failed'] += 1
        
        return results
    
    def track_response(self, youtube_handle: str, response_content: str) -> bool:
        """Track a response received from a YouTube creator"""
        try:
            # Find the most recent message to this handle
            message = YouTubeMessage.objects.filter(
                target_youtube_handle__iexact=youtube_handle.lstrip('@'),
                status__in=['sent', 'delivered']
            ).order_by('-sent_at').first()
            
            if message:
                message.mark_as_replied(response_content)
                
                # Also log in CommunicationLog
                CommunicationLog.objects.create(
                    customer=message.customer,
                    channel='youtube',
                    subject=f"Re: {message.subject}",
                    content=response_content,
                    is_outbound=False,  # This is a received message
                    external_message_id=message.external_message_id
                )
                
                return True
            return False
        except Exception as e:
            logger.error(f"Error tracking response from @{youtube_handle}: {str(e)}")
            return False


# Global instance
youtube_service = YouTubeMessagingService()