from django import forms
from .models import TripPlanRequest, Destination
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class TripPlanRequestForm(forms.ModelForm):
    class Meta:
        model = TripPlanRequest
        fields = ['destination', 'duration', 'budget', 'number_of_travelers', 'interests', 'daily_budget', 'transportation_preferences', 'experience_style', 'uploaded_file']
        widgets = {
            'destination': forms.Select(attrs={'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'number_of_travelers': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'daily_budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'transportation_preferences': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_style': forms.TextInput(attrs={'class': 'form-control'}),
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
