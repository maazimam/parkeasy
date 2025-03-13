from django import forms
from django.forms import inlineformset_factory
from .models import Booking, BookingSlot

# If you want half-hour dropdowns for booking times:
HALF_HOUR_CHOICES = [
    (f"{hour:02d}:{minute:02d}", f"{hour:02d}:{minute:02d}")
    for hour in range(24)
    for minute in (0, 30)
]

class BookingForm(forms.ModelForm):
    """If you have fields on Booking that the user can fill out (e.g., no extra fields?), keep empty."""
    class Meta:
        model = Booking
        fields = []  # No direct fields to fill, or you could add 'status' etc.

class BookingSlotForm(forms.ModelForm):
    start_time = forms.ChoiceField(choices=HALF_HOUR_CHOICES)
    end_time   = forms.ChoiceField(choices=HALF_HOUR_CHOICES)

    class Meta:
        model = BookingSlot
        fields = ["start_date", "start_time", "end_date", "end_time"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

BookingSlotFormSet = inlineformset_factory(
    Booking,
    BookingSlot,
    form=BookingSlotForm,
    extra=1,
    can_delete=True
)
