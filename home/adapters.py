from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_field, user_username
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter to handle Google OAuth user profile data
    """
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save user with Google profile data
        """
        user = super().save_user(request, sociallogin, form)
        
        # Get extra data from Google
        extra_data = sociallogin.account.extra_data
        
        # Update user fields with Google data
        if extra_data:
            # Set basic profile information
            if 'given_name' in extra_data:
                user.first_name = extra_data.get('given_name', '')
            if 'family_name' in extra_data:
                user.last_name = extra_data.get('family_name', '')
            
            # Store Google-specific data
            user.google_id = extra_data.get('id', '')
            user.avatar_url = extra_data.get('picture', '')
            user.is_google_user = True
            user.google_profile_data = extra_data
            
            # Set username from email if not set
            if not user.username and user.email:
                # Create username from email (before @ symbol)
                username = user.email.split('@')[0]
                # Make sure username is unique
                counter = 1
                original_username = username
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                user.username = username
            
            user.save()
        
        return user
    
    def populate_user(self, request, sociallogin, data):
        """
        Hook for populating user from social account data
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Additional population logic can go here
        extra_data = sociallogin.account.extra_data
        
        if extra_data:
            # Set email verified if from Google
            user.email_verified = True
        
        return user
