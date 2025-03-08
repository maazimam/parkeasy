from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Listing
from ..forms import ListingForm
from datetime import datetime, timedelta, time


class ListingsViewsTests(TestCase):
    def setUp(self):
        """Set up a test client and create a test user and listing."""
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

        # Ensure valid available dates (available_from < available_until)
        self.listing = Listing.objects.create(
            user=self.user,
            title="Test Listing",
            location="Test Location [123, 456]",
            rent_per_hour=10.0,
            available_from=datetime.now().date(),  # Today
            available_until=(datetime.now() + timedelta(days=2)).date(),  # Future date
            available_time_from=time(9, 0),  # 9:00 AM
            available_time_until=time(17, 0),  # 5:00 PM
            description="Test Description",
        )

    def test_create_listing_view_get(self):
        """Test that the create listing view loads correctly."""
        response = self.client.get(reverse("create_listing"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/create_listing.html")
        self.assertIsInstance(response.context["form"], ListingForm)

    def test_create_listing_view_post(self):
        """Test successful listing creation with valid data."""
        response = self.client.post(
            reverse("create_listing"),
            {
                "title": "New Listing",
                "description": "New Description",
                "rent_per_hour": 15.0,
                "available_from": datetime.now().date(),  # Today
                "available_until": (
                    datetime.now() + timedelta(days=2)
                ).date(),  # Future
                "available_time_from": "09:00",
                "available_time_until": "17:00",
                "location": "New Location [123, 456]",
            },
        )
        self.assertEqual(response.status_code, 302)  # Expect redirect
        self.assertRedirects(response, reverse("view_listings"))
        self.assertTrue(Listing.objects.filter(title="New Listing").exists())

    def test_view_listings_view(self):
        """Test that the view listings page loads correctly."""
        response = self.client.get(reverse("view_listings"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/view_listings.html")

    def test_manage_listings_view(self):
        """Test that the manage listings page loads correctly."""
        response = self.client.get(reverse("manage_listings"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/manage_listings.html")

    def test_edit_listing_view_get(self):
        """Test that the edit listing view loads correctly."""
        response = self.client.get(reverse("edit_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/edit_listing.html")

    def test_edit_listing_view_post(self):
        """Test successful listing edit with valid data."""
        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]),
            {
                "title": "Updated Listing",
                "description": "Updated Description",
                "rent_per_hour": 20.0,
                "available_from": datetime.now().date(),
                "available_until": (
                    datetime.now() + timedelta(days=3)
                ).date(),  # Future
                "available_time_from": "10:00",
                "available_time_until": "16:00",
                "location": "Updated Location [789, 321]",
            },
        )
        self.assertEqual(response.status_code, 302)  # Expect redirect
        self.assertRedirects(response, reverse("manage_listings"))
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, "Updated Listing")  # Ensure update applied

    def test_delete_listing_view_get(self):
        """Test that the delete listing confirmation page loads correctly."""
        response = self.client.get(reverse("delete_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/confirm_delete.html")

    def test_delete_listing_view_post(self):
        """Test successful listing deletion."""
        response = self.client.post(reverse("delete_listing", args=[self.listing.id]))
        self.assertEqual(response.status_code, 302)  # Expect redirect
        self.assertRedirects(response, reverse("manage_listings"))
        self.assertFalse(
            Listing.objects.filter(id=self.listing.id).exists()
        )  # Ensure deletion

    def test_listing_reviews_view(self):
        """Test that the listing reviews page loads correctly."""
        response = self.client.get(reverse("listing_reviews", args=[self.listing.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/listing_reviews.html")
