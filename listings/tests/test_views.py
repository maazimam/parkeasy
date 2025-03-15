from datetime import datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import ListingForm, ListingSlotFormSet
from ..models import Listing, ListingSlot




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
            data.update(
                {
                    f"{prefix}-0-start_date": "2025-03-12",
                    f"{prefix}-0-start_time": "10:00",
                    f"{prefix}-0-end_date": "2025-03-12",
                    f"{prefix}-0-end_time": "12:00",
                }
            )
        return data

    def test_create_listing_get(self):
        url = reverse("create_listing")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/create_listing.html")
        self.assertIsInstance(response.context["form"], ListingForm)

    def test_create_listing_view_post(self):
        tomorrow = datetime.now().date() + timedelta(days=1)
        response = self.client.post(
            reverse("create_listing"),
            {
                "title": "New Listing",
                "description": "New Description",
                "rent_per_hour": 15.0,
                "available_from": tomorrow,
                "available_until": tomorrow,
                "available_time_from": "09:00",  # 9:00 AM
                "available_time_until": "17:00",  # 5:00 PM
                "location": "New Location [123, 456]",
            },
        )
        if response.status_code != 302:
            print(
                response.context["form"].errors
            )  # Print form errors if the status code is not 302
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("view_listings"))
        self.assertTrue(Listing.objects.filter(title="New Listing").exists())

    def test_view_listings_view(self):
        response = self.client.get(reverse("view_listings"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/view_listings.html")

    def test_manage_listings_view(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("manage_listings"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/manage_listings.html")

    def test_edit_listing_view_get(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("edit_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/edit_listing.html")

    def test_edit_listing_view_post(self):
        self.client.login(username="testuser", password="12345")
        tomorrow = datetime.now().date() + timedelta(days=1)
        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]),
            {
                "title": "Updated Listing",
                "description": "Updated Description",
                "rent_per_hour": 20.0,
                "available_from": tomorrow,
                "available_until": tomorrow,
                "available_time_from": "09:00",  # 9:00 AM
                "available_time_until": "17:00",  # 5:00 PM
                "location": "Updated Location [123, 456]",
            },
        )
        if response.status_code != 302:
            print(
                response.context["form"].errors
            )  # Print form errors if the status code is not 302
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("manage_listings"))
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, "Updated Listing")

    def test_delete_listing_view_get(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("delete_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/confirm_delete.html")

    def test_delete_listing_view_post(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.post(reverse("delete_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("manage_listings"))

    def test_listing_reviews_view(self):
        response = self.client.get(reverse("listing_reviews", args=[self.listing.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/listing_reviews.html")


class ListingsFilterTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")

        # Set a fixed "now" time for testing
        self.test_now = datetime(2025, 3, 15, 14, 30)  # March 15, 2025, 2:30 PM
        self.test_date = self.test_now.date()
        self.test_time = self.test_now.time()

    @patch("listings.views.datetime")
    def test_listing_time_filtering(self, mock_datetime):
        # Mock datetime.now() to return our fixed test time
        mock_datetime.now.return_value = self.test_now

        # Create test listings with various date/time combinations

        # 1. Future date - should be included
        _ = Listing.objects.create(
            user=self.user,
            title="Future Listing",
            location="Future Location",
            rent_per_hour=10.0,
            description="This should be included",
            available_from=self.test_date,
            available_until=self.test_date + timedelta(days=5),  # 5 days in future
            available_time_from=time(9, 0),
            available_time_until=time(17, 0),
        )

        # 2. Today with future time - should be included
        _ = Listing.objects.create(
            user=self.user,
            title="Today Future Time",
            location="Today Location",
            rent_per_hour=10.0,
            description="This should be included",
            available_from=self.test_date - timedelta(days=5),
            available_until=self.test_date,  # Today
            available_time_from=time(9, 0),
            available_time_until=time(17, 0),  # 5:00 PM (after our test time)
        )

        # 3. Today with past time - should be excluded
        _ = Listing.objects.create(
            user=self.user,
            title="Today Past Time",
            location="Today Past Location",
            rent_per_hour=10.0,
            description="This should be excluded",
            available_from=self.test_date - timedelta(days=5),
            available_until=self.test_date,  # Today
            available_time_from=time(9, 0),
            available_time_until=time(12, 0),  # 12:00 PM (before our test time)
        )

        # 4. Past date - should be excluded
        _ = Listing.objects.create(
            user=self.user,
            title="Past Listing",
            location="Past Location",
            rent_per_hour=10.0,
            description="This should be excluded",
            available_from=self.test_date - timedelta(days=10),
            available_until=self.test_date - timedelta(days=1),  # Yesterday
            available_time_from=time(9, 0),
            available_time_until=time(17, 0),
        )

        # Access the view
        response = self.client.get(reverse("view_listings"))

        # Get listings from context
        context_listings = response.context["listings"]
        listing_titles = [listing.title for listing in context_listings]

        # Verify correct listings are included/excluded
        self.assertIn("Future Listing", listing_titles)
        self.assertIn("Today Future Time", listing_titles)
        self.assertNotIn("Today Past Time", listing_titles)
        self.assertNotIn("Past Listing", listing_titles)

        # Also check by count - should be exactly 2 listings
        self.assertEqual(len(context_listings), 2)


class ListingOwnerBookingTest(TestCase):
    def setUp(self):
        # Create two users: owner and non-owner
        self.owner = User.objects.create_user(username="owner", password="ownerpass123")
        self.non_owner = User.objects.create_user(
            username="renter", password="renterpass123"
        )

        # Create a listing owned by the owner
        self.listing = Listing.objects.create(
            user=self.owner,
            title="Test Parking Spot",
            location="Test Location [123.456, 789.012]",
            rent_per_hour=10.0,
            description="Test Description",
            available_from=(datetime.now() - timedelta(days=1)).date(),
            available_until=(datetime.now() + timedelta(days=30)).date(),
            available_time_from=time(9, 0),
            available_time_until=time(17, 0),
        )

        # URL for viewing listings
        self.view_listings_url = reverse("view_listings")

    def test_owner_sees_badge_not_book_button(self):
        """Test that owners see 'Your listing' badge instead of 'Book Now' button"""
        self.client.login(username="owner", password="ownerpass123")
        response = self.client.get(self.view_listings_url)
        self.assertEqual(response.status_code, 200)

        # Check for badge content and class, ignoring exact HTML structure
        self.assertContains(response, "Your listing")
        self.assertContains(response, 'class="badge bg-secondary"')

        # Check that Book Now button is NOT present for this listing
        book_url = reverse("book_listing", args=[self.listing.id])
        self.assertNotContains(response, f'href="{book_url}"')
        self.assertNotContains(response, "Book Now")

    def test_non_owner_sees_book_button(self):
        """Test that non-owners see the 'Book Now' button"""
        self.client.login(username="renter", password="renterpass123")
        response = self.client.get(self.view_listings_url)
        self.assertEqual(response.status_code, 200)

        # Check that 'Your listing' badge is NOT present
        self.assertNotContains(response, "Your listing")

        # Check for Book Now button elements without being strict about HTML structure
        book_url = reverse("book_listing", args=[self.listing.id])
        self.assertContains(response, f'href="{book_url}"')
        self.assertContains(response, 'class="btn btn-success')
        self.assertContains(response, "Book Now")
