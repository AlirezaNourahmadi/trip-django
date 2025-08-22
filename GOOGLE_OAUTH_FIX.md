# Google OAuth Configuration Fix

## The Issue
You're seeing the error: `Error 400: redirect_uri_mismatch` because the redirect URI in your Google Console doesn't match what Django is sending.

## Solution

### 1. Update Google Console Settings

Go to [Google Cloud Console](https://console.cloud.google.com/):

1. **Navigate to your project** → APIs & Services → Credentials
2. **Click on your OAuth 2.0 Client ID**
3. **In the "Authorized redirect URIs" section, add these URLs:**

   ```
   http://127.0.0.1:8000/accounts/google/login/callback/
   http://localhost:8000/accounts/google/login/callback/
   ```

   For production, also add:
   ```
   https://yourdomain.com/accounts/google/login/callback/
   ```

4. **Save the changes**

### 2. Verify Django Site Configuration

The Django site domain has been updated to `127.0.0.1:8000` to match the redirect URI.

Current configuration:
- **Site Domain**: `127.0.0.1:8000`
- **Site Name**: `TripAI Development`
- **Expected Callback URL**: `http://127.0.0.1:8000/accounts/google/login/callback/`

### 3. Test the OAuth Flow

1. Go to your login page: `http://127.0.0.1:8000/accounts/login/`
2. Click "Get Started with Google"
3. You should now see the beautiful OAuth confirmation page
4. Click "Continue with Google" to complete the authentication

### 4. Common Issues & Solutions

#### Issue: Still getting redirect_uri_mismatch
**Solution**: Double-check that the URLs in Google Console exactly match:
- Include the trailing slash `/`
- Use `127.0.0.1` instead of `localhost` (or add both)
- Ensure the port number matches (`:8000`)

#### Issue: OAuth page is not styled
**Solution**: The template is now created at:
`home/templates/socialaccount/providers/google/login.html`

#### Issue: SSL certificate errors in development
**Solution**: Use `http://` for local development, `https://` only for production.

### 5. Production Deployment Notes

When deploying to production:

1. **Update the Site domain** in Django admin:
   ```python
   from django.contrib.sites.models import Site
   site = Site.objects.get(id=1)
   site.domain = 'yourdomain.com'
   site.name = 'TripAI Production'
   site.save()
   ```

2. **Add production redirect URI** to Google Console:
   ```
   https://yourdomain.com/accounts/google/login/callback/
   ```

3. **Update environment variables** for production OAuth credentials.

### 6. Security Best Practices

- ✅ Use HTTPS in production
- ✅ Restrict OAuth redirect URIs to your domains only
- ✅ Keep OAuth secrets secure and never commit them to version control
- ✅ Regularly rotate OAuth credentials
- ✅ Monitor OAuth usage in Google Console

---

## Files Created/Modified

1. **`home/templates/socialaccount/providers/google/login.html`** - Beautiful OAuth confirmation page
2. **Django Site domain updated** - To match redirect URI
3. **This documentation file** - For future reference

The OAuth flow should now work perfectly with a beautiful, modern interface that matches your app's design! 🚀
