# listings/forms.py
from django import forms

from .models import Listing


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'location', 'rent_per_hour', 'description',
                  'available_from', 'available_until',
                  'available_time_from', 'available_time_until']
        widgets = {
            'available_from': forms.DateInput(attrs={'type': 'date'}),
            'available_until': forms.DateInput(attrs={'type': 'date'}),
            'available_time_from': forms.TimeInput(attrs={'type': 'time'}),
            'available_time_until': forms.TimeInput(attrs={'type': 'time'}),
        }
