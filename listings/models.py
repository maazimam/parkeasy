# listings/models.py

from django.contrib.auth.models import User
from django.db import models


class Listing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    rent_per_hour = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.TextField(max_length=500)

    # Availability dates
    available_from = models.DateField(null=True, blank=True)
    available_until = models.DateField(null=True, blank=True)

    # Daily availability times
    available_time_from = models.TimeField()
    available_time_until = models.TimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.location}"

    class Meta:
        ordering = ['-created_at']
