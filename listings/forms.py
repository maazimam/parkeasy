# listings/forms.py
from django import forms
from .models import Listing

class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['location', 'rent_per_hour', 'additional_info']
