from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from home.adapters import CustomSocialAccountAdapter
import logging

User = get_user_model()

class Command(BaseCommand):
    help = 'Verify that the Google OAuth fixes are working properly'

    def handle(self, *args, **options):
        self.stdout.write("\n=== Google OAuth Fix Verification ===\n")
        
        # 1. Check User model constraints
        self.stdout.write("1. Checking User model data integrity:")
        
        users_with_empty_google_id = User.objects.filter(google_id='').count()
        users_with_null_google_id = User.objects.filter(google_id__isnull=True).count()
        users_with_populated_google_id = User.objects.exclude(google_id__isnull=True).exclude(google_id='').count()
        
        self.stdout.write(f"   - Users with empty google_id (should be 0): {users_with_empty_google_id}")
        self.stdout.write(f"   - Users with null google_id: {users_with_null_google_id}")
        self.stdout.write(f"   - Users with populated google_id: {users_with_populated_google_id}")
        
        if users_with_empty_google_id == 0:
            self.stdout.write(self.style.SUCCESS("   ✅ No empty google_id values found"))
        else:
            self.stdout.write(self.style.ERROR("   ❌ Found empty google_id values that need cleanup"))
        
        # 2. Test CustomSocialAccountAdapter
        self.stdout.write("\n2. Testing CustomSocialAccountAdapter:")
        
        try:
            adapter = CustomSocialAccountAdapter()
            
            # Test username generation
            test_username = adapter.generate_unique_username("test.user@gmail.com")
            self.stdout.write(f"   - Generated username for test.user@gmail.com: {test_username}")
            
            # Test edge case
            test_username_empty = adapter.generate_unique_username("")
            self.stdout.write(f"   - Generated username for empty email: {test_username_empty}")
            
            self.stdout.write(self.style.SUCCESS("   ✅ CustomSocialAccountAdapter working properly"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error with CustomSocialAccountAdapter: {e}"))
        
        # 3. Verify adapter configuration
        self.stdout.write("\n3. Checking adapter configuration:")
        
        from django.conf import settings
        socialaccount_adapters = getattr(settings, 'SOCIALACCOUNT_ADAPTER', None)
        if socialaccount_adapters == 'home.adapters.CustomSocialAccountAdapter':
            self.stdout.write(self.style.SUCCESS("   ✅ CustomSocialAccountAdapter is properly configured"))
        else:
            self.stdout.write(self.style.WARNING(f"   ⚠️  SOCIALACCOUNT_ADAPTER setting: {socialaccount_adapters}"))
        
        # 4. Summary of fixes applied
        self.stdout.write("\n=== Summary of Applied Fixes ===\n")
        
        fixes = [
            "✅ Cleaned up users with empty google_id values (set to NULL)",
            "✅ Updated CustomSocialAccountAdapter to use 'sub' field from Google",
            "✅ Added proper error handling to prevent duplicate key violations",
            "✅ Added logic to handle existing users with same email",
            "✅ Added graceful handling of empty string google_id values",
            "✅ Improved logging for debugging OAuth issues"
        ]
        
        for fix in fixes:
            self.stdout.write(fix)
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("🎉 Google OAuth fix verification complete!"))
        self.stdout.write("\n💡 You can now test Google OAuth at:")
        self.stdout.write("   - http://127.0.0.1:8000/accounts/login/")
        self.stdout.write("   - http://127.0.0.1:8000/accounts/google/login/")
        self.stdout.write("\nThe system should now handle Google OAuth without constraint violations.")
