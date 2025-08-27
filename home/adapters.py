from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_field, user_username
from django.contrib.auth import get_user_model
import logging
import uuid

User = get_user_model()
logger = logging.getLogger(__name__)

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter to handle Google OAuth user profile data
    """
    
    def generate_unique_username(self, email):
        """
        Generate a unique username from email
        """
        if not email:
            # Fallback for cases without email
            base_username = f"user_{uuid.uuid4().hex[:8]}"
        else:
            # Create username from email (before @ symbol)
            base_username = email.split('@')[0]
        
        # Clean username (remove special characters)
        import re
        base_username = re.sub(r'[^a-zA-Z0-9_]', '', base_username)
        
        # Ensure it's not empty
        if not base_username:
            base_username = f"user_{uuid.uuid4().hex[:8]}"
        
        # Make sure username is unique
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username
    
    def populate_user(self, request, sociallogin, data):
        """
        Hook for populating user from social account data
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Get extra data from Google
        extra_data = sociallogin.account.extra_data
        logger.info(f"Google OAuth extra_data: {extra_data}")
        
        if extra_data:
            # Set basic profile information
            if 'given_name' in extra_data:
                user.first_name = extra_data.get('given_name', '')
            if 'family_name' in extra_data:
                user.last_name = extra_data.get('family_name', '')
        
        # CRITICAL: Ensure username is set and unique BEFORE saving
        if not user.username or user.username == '':
            user.username = self.generate_unique_username(user.email)
            logger.info(f"Generated username: {user.username} for email: {user.email}")
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save user with Google profile data
        """
        try:
            # Get extra data from Google
            extra_data = sociallogin.account.extra_data
            google_id = extra_data.get('sub', None) if extra_data else None
            
            # IMPORTANT: Make sure google_id is not an empty string
            if google_id == '':
                google_id = None
                logger.warning("Empty string google_id detected, setting to None")
            
            # Skip the google_id check if it's None
            if google_id:
                # Check if user with this google_id already exists
                existing_user = User.objects.filter(google_id=google_id).first()
                if existing_user:
                    logger.info(f"User with google_id {google_id} already exists: {existing_user.email}")
                    return existing_user
                
                # Also check if a user with this email already exists
                email = sociallogin.account.user.email
                if email:
                    existing_email_user = User.objects.filter(email=email).first()
                    if existing_email_user:
                        # Update the existing user with the google_id
                        logger.info(f"User with email {email} already exists, updating with google_id {google_id}")
                        existing_email_user.google_id = google_id
                        existing_email_user.is_google_user = True
                        existing_email_user.avatar_url = extra_data.get('picture', '')
                        existing_email_user.google_profile_data = extra_data
                        existing_email_user.save()
                        return existing_email_user
            
            # Create new user
            user = super().save_user(request, sociallogin, form)
            
            # Update user fields with Google data (post-save)
            if extra_data and google_id:
                try:
                    # Store Google-specific data
                    user.google_id = google_id  # Use 'sub' field which is the Google user ID
                    user.avatar_url = extra_data.get('picture', '')
                    user.is_google_user = True
                    user.google_profile_data = extra_data
                    
                    user.save()
                    logger.info(f"Successfully saved Google user: {user.email} with username: {user.username} and google_id: {google_id}")
                except Exception as e:
                    # Handle potential database errors gracefully
                    logger.error(f"Error updating user with Google data: {e}")
                    # If saving with google_id fails, still return the created user
            
            return user
            
        except Exception as e:
            logger.error(f"Error saving Google OAuth user: {e}")
            raise
