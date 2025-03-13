from django.db import models
from django.contrib.auth.models import User
from listings.models import Listing


class Booking(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("DECLINED", "Declined"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking #{self.pk} by {self.user.username} for {self.listing.title}"


class BookingSlot(models.Model):
    """
    A single interval of time within a booking.
    E.g. from 3/14 13:00 to 3/14 17:00,
    or from 3/30 10:00 to 3/30 12:00, etc.
    """

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="slots")
    start_date = models.DateField()
    start_time = models.TimeField()
    end_date = models.DateField()
    end_time = models.TimeField()

    def __str__(self):
        return (
            f"BookingSlot for Booking #{self.booking.pk}: "
            f"{self.start_date} {self.start_time} - {self.end_date} {self.end_time}"
        )
