# Google OAuth 2.0 Setup Guide for TripAI

This guide will help you set up Google OAuth 2.0 authentication for your Django TripAI application.

## Prerequisites

1. A Google account
2. Access to Google Cloud Console
3. Your Django application running locally or on a server

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click "NEW PROJECT"
4. Enter your project name (e.g., "TripAI")
5. Select your organization if applicable
6. Click "CREATE"

## Step 2: Enable the Google+ API (or Google Identity Services)

1. In the Google Cloud Console, navigate to "APIs & Services" → "Library"
2. Search for "Google+ API" or "Google Identity Services API"
3. Click on it and press "ENABLE"
4. Alternatively, you can enable "People API" for more profile information

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Select "External" (unless you have Google Workspace)
3. Fill in the required fields:
   - **App name**: TripAI
   - **User support email**: Your email
   - **Developer contact information**: Your email
4. Add your domain to "Authorized domains" if deploying to production
5. Add scopes (usually the default ones are enough):
   - `openid`
   - `email` 
   - `profile`
6. Save and continue through the remaining steps

## Step 4: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "+ CREATE CREDENTIALS" → "OAuth client ID"
3. Select "Web application" as the application type
4. Configure the following:
   - **Name**: TripAI Web Client
   - **Authorized JavaScript origins**: 
     - `http://localhost:8000` (for development)
     - `http://127.0.0.1:8000` (for development)
     - Your production domain (when deploying)
   - **Authorized redirect URIs**:
     - `http://localhost:8000/accounts/google/login/callback/` (for development)
     - `http://127.0.0.1:8000/accounts/google/login/callback/` (for development)
     - `https://yourdomain.com/accounts/google/login/callback/` (for production)
5. Click "CREATE"
6. Copy the **Client ID** and **Client Secret**

## Step 5: Configure Django Settings

1. Open your `.env` file in your Django project
2. Replace the placeholder values with your actual credentials:

```env
# Google OAuth2 Configuration
GOOGLE_OAUTH2_CLIENT_ID=your_actual_google_client_id_here
GOOGLE_OAUTH2_CLIENT_SECRET=your_actual_google_client_secret_here
```

## Step 6: Add Social Application in Django Admin

1. Run your Django server: `python manage.py runserver`
2. Go to `http://localhost:8000/admin/`
3. Log in with a superuser account (create one if needed: `python manage.py createsuperuser`)
4. Navigate to "Social Applications" under "Social Accounts"
5. Click "Add Social Application"
6. Fill in the form:
   - **Provider**: Google
   - **Name**: Google OAuth
   - **Client id**: Your Google Client ID
   - **Secret key**: Your Google Client Secret
   - **Sites**: Select "example.com" or create/select your site
7. Save the application

## Step 7: Update Site Configuration

1. In Django admin, go to "Sites"
2. Edit the existing site (usually "example.com")
3. Change:
   - **Domain name**: `localhost:8000` (for development) or your actual domain
   - **Display name**: TripAI
4. Save the changes

## Testing the Implementation

1. Start your Django server: `python manage.py runserver`
2. Go to `http://localhost:8000/accounts/login/`
3. You should see the login page with a "Continue with Google" button
4. Click the Google login button
5. You should be redirected to Google's OAuth consent screen
6. After authorizing, you should be redirected back to your application and logged in

## Production Deployment Notes

When deploying to production:

1. Update the `.env` file with production values
2. Add your production domain to Google Cloud Console OAuth settings
3. Update the Django Site object with your production domain
4. Ensure HTTPS is enabled for production
5. Update `ALLOWED_HOSTS` in Django settings

## Troubleshooting

### Common Issues:

1. **"redirect_uri_mismatch" error**: 
   - Make sure the redirect URI in Google Console exactly matches the one Django is using
   - Include the trailing slash in the redirect URI

2. **"invalid_client" error**: 
   - Check that your Client ID and Secret are correct
   - Make sure the Social Application is properly configured in Django admin

3. **"access_denied" error**: 
   - User cancelled the authorization
   - Check OAuth consent screen configuration

4. **Site not found error**: 
   - Make sure the Site object in Django admin is properly configured
   - Ensure SITE_ID in settings matches the correct site

## Features Included

Your Google OAuth integration includes:

- ✅ Google OAuth login/signup
- ✅ Automatic user profile creation with Google data
- ✅ Avatar images from Google profiles
- ✅ First name and last name from Google
- ✅ Email verification bypass for Google users
- ✅ Custom welcome messages for new/returning Google users
- ✅ Fallback to traditional email/password authentication
- ✅ User profile data synchronization with Google

## Security Notes

- Never commit your `.env` file with real credentials to version control
- Use environment variables for all sensitive configuration
- Enable HTTPS in production
- Regularly review and rotate OAuth credentials
- Monitor OAuth usage in Google Cloud Console

For more detailed information, refer to the [django-allauth documentation](https://django-allauth.readthedocs.io/).
