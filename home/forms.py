from django import forms
from .models import TripPlanRequest
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

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
