import datetime as dt
from django.db import models
from django.contrib.auth.models import User


class Listing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    rent_per_hour = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / reviews.count()
        return None

    def __str__(self):
        return f"{self.title} - {self.location}"

    def is_available_for_range(self, start_dt, end_dt):
        """
        Return True if this listing's combined ListingSlot intervals
        cover the entire range [start_dt, end_dt).
        """
        intervals = []
        for slot in self.slots.all():
            slot_start = dt.datetime.combine(slot.start_date, slot.start_time)
            slot_end = dt.datetime.combine(slot.end_date, slot.end_time)
            intervals.append((slot_start, slot_end))
        intervals.sort(key=lambda iv: iv[0])
        merged = []
        for interval in intervals:
            if not merged:
                merged.append(interval)
            else:
                last_start, last_end = merged[-1]
                this_start, this_end = interval
                if this_start <= last_end:
                    merged[-1] = (last_start, max(last_end, this_end))
                else:
                    merged.append(interval)
        coverage_start = start_dt
        for iv_start, iv_end in merged:
            if iv_start <= coverage_start < iv_end:
                if iv_end >= end_dt:
                    return True
                coverage_start = iv_end
            elif iv_start > coverage_start:
                return False
        return False


class ListingSlot(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="slots")
    start_date = models.DateField()
    start_time = models.TimeField()
    end_date = models.DateField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.listing.title} slot: {self.start_date} {self.start_time} - {self.end_date} {self.end_time}"


class Review(models.Model):
    # Use a one-to-one relation to Booking so that each booking gets one review
    booking = models.OneToOneField(
        "booking.Booking", on_delete=models.CASCADE, related_name="review"
    )
    # Redundant but handy: directly link to the listing being reviewed
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # For the star rating (e.g. 1 to 5)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(max_length=1000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.listing.title} by {self.user.username}"
