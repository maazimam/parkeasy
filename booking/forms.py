# booking/forms.py
from django import forms
from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["booking_date", "start_time", "end_time"]
        widgets = {
            "booking_date": forms.DateInput(attrs={"type": "date"}),
            # 'start_time' and 'end_time' will be updated dynamically in __init__
        }

    def __init__(self, *args, **kwargs):
        # Pop the listing object (if provided)
        listing = kwargs.pop("listing", None)
        super().__init__(*args, **kwargs)
        # Update the start_time and end_time widgets with time type and min/max attributes
        if listing:
            time_format = "%H:%M"
            self.fields["start_time"].widget = forms.TimeInput(
                attrs={
                    "type": "time",
                    "min": listing.available_time_from.strftime(time_format),
                    "max": listing.available_time_until.strftime(time_format),
                }
            )
            self.fields["end_time"].widget = forms.TimeInput(
                attrs={
                    "type": "time",
                    "min": listing.available_time_from.strftime(time_format),
                    "max": listing.available_time_until.strftime(time_format),
                }
            )
