from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added, social_account_updated
from allauth.account.signals import user_logged_in
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(social_account_added)
def social_account_added_handler(sender, request, sociallogin, **kwargs):
    """
    Handle when a new social account is added (first time Google login)
    """
    user = sociallogin.user
    
    # Send welcome message for new Google users
    if user.is_google_user and request:
        messages.success(
            request, 
            f"Welcome to TripAI, {user.first_name or user.username}! "
            f"Your Google account has been successfully linked."
        )

@receiver(social_account_updated)  
def social_account_updated_handler(sender, request, sociallogin, **kwargs):
    """
    Handle when an existing social account is updated
    """
    user = sociallogin.user
    extra_data = sociallogin.account.extra_data
    
    # Update profile data from Google if changed
    if extra_data:
        updated_fields = []
        
        if user.avatar_url != extra_data.get('picture', ''):
            user.avatar_url = extra_data.get('picture', '')
            updated_fields.append('avatar')
        
        if user.first_name != extra_data.get('given_name', ''):
            user.first_name = extra_data.get('given_name', '')
            updated_fields.append('first_name')
            
        if user.last_name != extra_data.get('family_name', ''):
            user.last_name = extra_data.get('family_name', '')
            updated_fields.append('last_name')
        
        # Update Google profile data
        user.google_profile_data = extra_data
        
        if updated_fields:
            user.save()
            if request:
                messages.info(
                    request,
                    f"Your profile has been updated from Google ({', '.join(updated_fields)})."
                )

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """
    Handle actions when user logs in (both social and regular)
    """
    if user.is_google_user and request:
        messages.success(
            request, 
            f"Welcome back, {user.first_name or user.username}! "
            f"Ready to plan your next adventure?"
        )
    elif request:
        messages.success(
            request, 
            f"Welcome back, {user.first_name or user.username}!"
        )
