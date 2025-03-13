# listings/tests.py
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ..models import Listing, ListingSlot, Review

# We use unittest.mock to patch the booking_set where needed.
from unittest.mock import patch, MagicMock


class ListingViewsTests(TestCase):
    def setUp(self):
        # Create a test user and log in.
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

        # Create a sample listing for tests that require an existing listing.
        self.listing = Listing.objects.create(
            user=self.user,
            title="Test Listing",
            location="Test Location [12.34, 56.78]",
            rent_per_hour=Decimal("10.00"),
            description="A test listing.",
        )
        # Create a listing slot for the sample listing.
        ListingSlot.objects.create(
            listing=self.listing,
            start_date="2025-03-12",
            start_time="10:00",
            end_date="2025-03-12",
            end_time="12:00",
        )

    def _build_slot_formset_data(self, prefix="form", count=1):
        """
        Helper method to build valid formset data for ListingSlotFormSet.
        Adjust keys based on your actual formset configuration.
        """
        data = {
            f"{prefix}-TOTAL_FORMS": str(count),
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
        }
        # For one slot form
        if count >= 1:
            data.update({
                f"{prefix}-0-start_date": "2025-03-12",
                f"{prefix}-0-start_time": "10:00",
                f"{prefix}-0-end_date": "2025-03-12",
                f"{prefix}-0-end_time": "12:00",
            })
        return data

    def test_create_listing_get(self):
        url = reverse("create_listing")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Check that both the listing form and the formset are in the context.
        self.assertIn("form", response.context)
        self.assertIn("slot_formset", response.context)
