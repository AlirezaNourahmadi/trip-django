from django import forms
from .models import TripPlanRequest
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from PIL import Image
import os

User = get_user_model()

class TripPlanRequestForm(forms.ModelForm):
    # Hidden fields for Google Places data
    destination_country = forms.CharField(widget=forms.HiddenInput(), required=False)
    destination_place_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    def clean_budget(self):
        budget = self.cleaned_data.get('budget')
        if budget is None:
            return budget
        try:
            if budget < 0:
                raise ValidationError("Budget cannot be negative.")
        except TypeError:
            raise ValidationError("Invalid budget value.")
        return budget
    
    class Meta:
        model = TripPlanRequest
        fields = ['destination', 'destination_country', 'destination_place_id', 'duration', 'budget', 'number_of_travelers', 'interests', 'daily_budget', 'transportation_preferences', 'experience_style', 'uploaded_file']
        widgets = {
            'destination': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'destination-input',
                'placeholder': 'e.g., Paris, France',
                'autocomplete': 'off'
            }),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'e.g., 7'}),
'budget': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 3,000', 'data-currency': 'USD', 'required': True, 'inputmode': 'decimal'}),
            'number_of_travelers': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'e.g., 2'}),
            'interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., History, Art, Food, Hiking'}),
'daily_budget': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auto-calculated', 'readonly': True}),
            'transportation_preferences': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Public transit, Walking, Ride-sharing'}),
            'experience_style': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Relaxing, Adventurous, Family-friendly, Luxury'}),
            'uploaded_file': forms.FileInput(attrs={'class': 'form-control'}),
        }

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class ChatMessageForm(forms.Form):
    message = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ask me about your trip...',
            'autocomplete': 'off'
        }),
        max_length=500,
        required=False
    )
    file_attachment = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.txt,.csv,.xlsx'
        })
    )
    voice_attachment = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.mp3,.wav,.ogg,.m4a'
        })
    )


# Profile Management Forms

class ProfilePictureForm(forms.ModelForm):
    """Form for uploading profile picture"""
    
    class Meta:
        model = User
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'profile-picture-input'
            })
        }
    
    def clean_profile_picture(self):
        """Validate uploaded profile picture"""
        picture = self.cleaned_data.get('profile_picture')
        
        if picture:
            # Check file size (5MB limit)
            if picture.size > 5 * 1024 * 1024:
                raise ValidationError('Image file too large. Maximum size is 5MB.')
            
            # Check file format
            valid_formats = ['JPEG', 'JPG', 'PNG', 'GIF', 'WEBP']
            try:
                img = Image.open(picture)
                if img.format not in valid_formats:
                    raise ValidationError(
                        f'Invalid image format. Supported formats: {", ".join(valid_formats)}'
                    )
            except Exception:
                raise ValidationError('Invalid image file.')
        
        return picture


class PersonalInfoForm(forms.ModelForm):
    """Form for updating personal information"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'bio', 'phone_number',
            'date_of_birth', 'location', 'website'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself...',
                'maxlength': 500
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, State/Country'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourwebsite.com'
            }),
        }
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if email and User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError('This email address is already in use.')
        return email
    
    def clean_phone_number(self):
        """Basic phone number validation"""
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove all non-digit characters for validation
            digits_only = ''.join(filter(str.isdigit, phone))
            if len(digits_only) < 10:
                raise ValidationError('Please enter a valid phone number.')
        return phone
    
    def clean_website(self):
        """Validate website URL"""
        website = self.cleaned_data.get('website')
        if website and not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        return website


class TravelPreferencesForm(forms.ModelForm):
    """Form for updating travel preferences"""
    
    BUDGET_RANGES = [
        ('', 'Select budget range'),
        ('budget', 'Budget (Under $100/day)'),
        ('mid-range', 'Mid-range ($100-300/day)'),
        ('luxury', 'Luxury ($300+/day)'),
        ('no-limit', 'No specific limit'),
    ]
    
    TRAVEL_STYLES = [
        ('', 'Select travel style'),
        ('adventure', 'Adventure & Outdoor'),
        ('cultural', 'Cultural & Historical'),
        ('relaxation', 'Relaxation & Wellness'),
        ('foodie', 'Food & Culinary'),
        ('nightlife', 'Nightlife & Entertainment'),
        ('family', 'Family-friendly'),
        ('solo', 'Solo Travel'),
        ('romantic', 'Romantic'),
        ('business', 'Business Travel'),
    ]
    
    # Override fields to add choices
    preferred_budget_range = forms.ChoiceField(
        choices=BUDGET_RANGES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    preferred_travel_style = forms.ChoiceField(
        choices=TRAVEL_STYLES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    ACCOMMODATION_TYPES = [
        ('', 'Select accommodation preference'),
        ('hotel', 'Hotels'),
        ('hostel', 'Hostels'),
        ('bnb', 'Bed & Breakfast'),
        ('apartment', 'Apartments/Airbnb'),
        ('resort', 'Resorts'),
        ('camping', 'Camping'),
        ('mixed', 'Mix of different types'),
    ]
    
    preferred_accommodations = forms.ChoiceField(
        choices=ACCOMMODATION_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    TRANSPORTATION_TYPES = [
        ('', 'Select transportation preference'),
        ('plane', 'Airplane'),
        ('train', 'Train'),
        ('car', 'Car/Road Trip'),
        ('bus', 'Bus'),
        ('mixed', 'Mixed Transportation'),
        ('local', 'Local Transport Only'),
    ]
    
    preferred_transportation = forms.ChoiceField(
        choices=TRANSPORTATION_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    travel_interests = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'e.g., Museums, Food tours, Adventure sports, Beach activities...'
        })
    )
    
    class Meta:
        model = User
        fields = [
            'preferred_budget_range', 'travel_style', 'previous_destinations',
            'dietary_restrictions'
        ]
        widgets = {
            'previous_destinations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List places you\'ve visited (e.g., Paris, Tokyo, New York...)'
            }),
            'dietary_restrictions': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Vegetarian, Vegan, Gluten-free, No allergies'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for choice fields from model
        if self.instance and self.instance.pk:
            self.fields['preferred_budget_range'].initial = self.instance.preferred_budget_range
            self.fields['preferred_travel_style'].initial = self.instance.travel_style
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Handle choice fields that aren't directly in Meta.fields
        user.preferred_budget_range = self.cleaned_data.get('preferred_budget_range')
        user.travel_style = self.cleaned_data.get('preferred_travel_style')
        
        if commit:
            user.save()
        return user


class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes and placeholders
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your new password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your new password'
        })
        
        # Update labels
        self.fields['old_password'].label = 'Current Password'
        self.fields['new_password1'].label = 'New Password'
        self.fields['new_password2'].label = 'Confirm New Password'


class DeleteAccountForm(forms.Form):
    """Form for account deletion confirmation"""
    
    confirm_deletion = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I understand that this action cannot be undone'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password to confirm'
        }),
        label='Password Confirmation'
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_password(self):
        """Verify password for account deletion"""
        password = self.cleaned_data.get('password')
        if password and not self.user.check_password(password):
            raise ValidationError('Incorrect password.')
        return password


class QuickProfileUpdateForm(forms.ModelForm):
    """Simplified form for quick profile updates"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Last name'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'Brief description...',
                'maxlength': 200
            }),
        }
