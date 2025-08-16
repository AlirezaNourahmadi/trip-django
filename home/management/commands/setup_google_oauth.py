from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os

class Command(BaseCommand):
    help = 'Set up Google OAuth social application'

    def handle(self, *args, **options):
        # Get Google OAuth credentials from environment
        client_id = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            self.stdout.write(
                self.style.ERROR('Google OAuth credentials not found in environment variables.')
            )
            self.stdout.write(
                self.style.ERROR('Please set GOOGLE_OAUTH2_CLIENT_ID and GOOGLE_OAUTH2_CLIENT_SECRET in your .env file.')
            )
            return
        
        # Update or create the Site object for localhost
        site, created = Site.objects.get_or_create(
            id=1,
            defaults={
                'domain': 'localhost:8000',
                'name': 'TripAI Development'
            }
        )
        
        if not created:
            site.domain = 'localhost:8000'
            site.name = 'TripAI Development'
            site.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated site: {site.domain}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Created site: {site.domain}')
            )
        
        # Create or update Google Social Application
        social_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google OAuth',
                'client_id': client_id,
                'secret': client_secret,
            }
        )
        
        if not created:
            social_app.client_id = client_id
            social_app.secret = client_secret
            social_app.save()
            self.stdout.write(
                self.style.SUCCESS('Updated existing Google OAuth application')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Created new Google OAuth application')
            )
        
        # Add the site to the social app
        social_app.sites.add(site)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Google OAuth setup complete!\n'
                f'Client ID: {client_id[:20]}...\n'
                f'Site: {site.domain}\n'
                f'You can now test Google OAuth at: http://localhost:8000/accounts/login/'
            )
        )
