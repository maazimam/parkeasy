# listings/forms.py
import datetime
import pytz
from django import forms
from django.utils import timezone
from django.forms import inlineformset_factory
from .models import Listing, ListingSlot, Review

# Generate half‑hour choices: "00:00", "00:30", …, "23:30"
HALF_HOUR_CHOICES = [
    (f"{hour:02d}:{minute:02d}", f"{hour:02d}:{minute:02d}")
    for hour in range(24)
    for minute in (0, 30)
]

class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ["title", "location", "rent_per_hour", "description"]
        # location can be updated by your map JS, etc.

class ListingSlotForm(forms.ModelForm):
    start_time = forms.ChoiceField(choices=HALF_HOUR_CHOICES)
    end_time   = forms.ChoiceField(choices=HALF_HOUR_CHOICES)

    class Meta:
        model = ListingSlot
        fields = ["start_date", "start_time", "end_date", "end_time"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

ListingSlotFormSet = inlineformset_factory(
    Listing,
    ListingSlot,
    form=ListingSlotForm,
    extra=1,
    can_delete=True
)





class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.NumberInput(
                attrs={"min": 1, "max": 5, "class": "form-control"}
            ),
            "comment": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        if rating < 1 or rating > 5:
            raise forms.ValidationError("Rating must be between 1 and 5")
        return rating
