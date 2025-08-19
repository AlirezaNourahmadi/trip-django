from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os

class Command(BaseCommand):
    help = 'Test Google OAuth configuration'

    def handle(self, *args, **options):
        # Check environment variables
        client_id = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET')
        
        self.stdout.write("\n=== Google OAuth Configuration Test ===\n")
        
        # Check credentials
        if client_id and client_secret:
            self.stdout.write(
                self.style.SUCCESS('✅ Google OAuth credentials found in environment')
            )
            self.stdout.write(f"Client ID: {client_id[:20]}...")
            self.stdout.write(f"Client Secret: {client_secret[:10]}...")
        else:
            self.stdout.write(
                self.style.ERROR('❌ Google OAuth credentials missing in environment')
            )
            return
        
        # Check Site configuration
        try:
            site = Site.objects.get(id=1)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Site configured: {site.domain} ({site.name})')
            )
        except Site.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Site not configured')
            )
            return
        
        # Check Social Application
        try:
            social_app = SocialApp.objects.get(provider='google')
            self.stdout.write(
                self.style.SUCCESS(f'✅ Google Social App configured: {social_app.name}')
            )
            
            # Check if site is associated
            if social_app.sites.filter(id=site.id).exists():
                self.stdout.write(
                    self.style.SUCCESS('✅ Social app is associated with the site')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Social app is not associated with the site')
                )
                
        except SocialApp.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Google Social App not configured')
            )
            return
        
        self.stdout.write("\n=== Required Google Cloud Console Configuration ===\n")
        self.stdout.write("Make sure you have configured the following in Google Cloud Console:")
        self.stdout.write("\n1. Authorized JavaScript origins:")
        self.stdout.write("   - http://localhost:8000")
        self.stdout.write("   - http://127.0.0.1:8000")
        
        self.stdout.write("\n2. Authorized redirect URIs:")
        self.stdout.write("   - http://localhost:8000/accounts/google/login/callback/")
        self.stdout.write("   - http://127.0.0.1:8000/accounts/google/login/callback/")
        
        self.stdout.write("\n=== Test URLs ===\n")
        self.stdout.write("Test your Google OAuth at:")
        self.stdout.write("- Login page: http://localhost:8000/accounts/login/")
        self.stdout.write("- Direct Google OAuth: http://localhost:8000/accounts/google/login/")
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write(
            self.style.SUCCESS("✅ Google OAuth configuration looks good!")
        )
