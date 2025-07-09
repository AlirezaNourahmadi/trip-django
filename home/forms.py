from django import forms
from .models  import TripPlanRequest
class TripPlanRequestForm(forms.Form):
    class Meta:
        model = TripPlanRequest
        fields = ['destination', 'start_date', 'end_date', 'preferences', 'budget', 'travelers', 'additional_info']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'preferences': forms.Textarea(attrs={'rows': 4}),
            'additional_info': forms.Textarea(attrs={'rows': 4}),
        }