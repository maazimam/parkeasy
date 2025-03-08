from django.test import TestCase
from datetime import date, timedelta
from ..forms import ListingForm, ReviewForm
import pytz
from django.utils import timezone

class ListingFormTest(TestCase):
    def setUp(self):
        """Set up valid form data for reuse."""
        self.valid_data = {
            "title": "Test Listing",
            "location": "Test Location",
            "rent_per_hour": 10,
            "description": "Test Description",
            "available_from": date.today() + timedelta(days=1),  # Future date
            "available_until": date.today() + timedelta(days=2),  # Future date
            "available_time_from": "08:00",
            "available_time_until": "18:00",
        }

    def test_listing_form_valid(self):
        """Test that a valid form passes."""
        form = ListingForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_listing_form_invalid_past_available_from(self):
        """Test available_from in the past should fail (NYC timezone)."""
        nyc_tz = pytz.timezone("America/New_York")
        today_nyc = timezone.now().astimezone(nyc_tz).date()  # Get NYC date

        data = self.valid_data.copy()
        data["available_from"] = today_nyc - timedelta(days=1)  # Past date in NYC
        form = ListingForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("available_from", form.errors)
        self.assertIn(
            "The 'Available From' date cannot be in the past.",
            form.errors["available_from"],
        )

    def test_listing_form_invalid_past_available_until(self):
        """Test available_until in the past should fail (NYC timezone)."""
        nyc_tz = pytz.timezone("America/New_York")
        today_nyc = timezone.now().astimezone(nyc_tz).date()  # Get NYC date

        data = self.valid_data.copy()
        data["available_until"] = today_nyc - timedelta(days=1)  # Past date in NYC
        form = ListingForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("available_until", form.errors)
        self.assertIn(
            "The 'Available Until' date cannot be in the past.",
            form.errors["available_until"],
        )

    def test_listing_form_invalid_available_until_before_available_from(self):
        """Test available_until before available_from should fail."""
        data = self.valid_data.copy()
        data["available_from"] = date.today() + timedelta(days=2)  # Future date
        data["available_until"] = date.today() + timedelta(
            days=1
        )  # Earlier than available_from

        form = ListingForm(data=data)
        self.assertFalse(form.is_valid())  # Ensure the form is invalid

        # Check that the error appears under "available_until" instead of "__all__"
        self.assertIn("available_until", form.errors)
        self.assertIn(
            "The 'Available Until' date cannot be before the 'Available From' date.",
            form.errors["available_until"],
        )

    def test_listing_form_invalid_rent_per_hour(self):
        """Test negative rent_per_hour should fail."""
        data = self.valid_data.copy()
        data["rent_per_hour"] = -5  # Invalid
        form = ListingForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn(
            "Rent per hour must be a positive number.", form.errors["__all__"]
        )

    def test_listing_form_invalid_time_range(self):
        """Test if available_time_from is after available_time_until on the same day, should fail."""
        data = self.valid_data.copy()
        data["available_from"] = data[
            "available_until"
        ] = date.today()  # Same-day booking
        data["available_time_from"] = "18:00"
        data["available_time_until"] = "08:00"  # Invalid: Ends before it starts
        form = ListingForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn(
            "For same-day bookings, end time must be after start time",
            form.errors["__all__"],
        )

    def test_listing_form_identical_time_range(self):
        """Test identical start and end time should fail."""
        data = self.valid_data.copy()
        data["available_time_from"] = "12:00"
        data["available_time_until"] = "12:00"  # Invalid
        form = ListingForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn(
            "Start and end times cannot be identical.", form.errors["__all__"]
        )


class ReviewFormTest(TestCase):
    def setUp(self):
        """Set up valid review data."""
        self.valid_data = {
            "rating": 5,
            "comment": "Great place!",
        }

    def test_review_form_valid(self):
        """Test a valid review form passes."""
        form = ReviewForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_review_form_invalid_rating_above_max(self):
        """Test rating above 5 should fail."""
        data = self.valid_data.copy()
        data["rating"] = 6  # Invalid
        form = ReviewForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("rating", form.errors)
        self.assertIn("Rating must be between 1 and 5.", form.errors["rating"])

    def test_review_form_invalid_rating_below_min(self):
        """Test rating below 1 should fail."""
        data = self.valid_data.copy()
        data["rating"] = 0  # Invalid
        form = ReviewForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("rating", form.errors)
        self.assertIn("Rating must be between 1 and 5.", form.errors["rating"])
