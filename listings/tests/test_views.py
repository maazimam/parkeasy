from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Listing
from ..forms import ListingForm
from datetime import datetime, time


class ListingsViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.user.profile.is_verified = True  # Ensure the user is verified
        self.user.profile.save()
        self.client.login(username="testuser", password="12345")
        self.listing = Listing.objects.create(
            user=self.user,
            title="Test Listing",
            location="Test Location [123, 456]",
            rent_per_hour=10.0,
            available_from=datetime.now().date(),
            available_until=datetime.now().date(),
            available_time_from=time(9, 0),  # 9:00 AM
            available_time_until=time(17, 0),  # 5:00 PM
            description="Test Description",
        )

    def test_create_listing_view_get(self):
        response = self.client.get(reverse("create_listing"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/create_listing.html")
        self.assertIsInstance(response.context["form"], ListingForm)

    def test_create_listing_view_post(self):
        response = self.client.post(
            reverse("create_listing"),
            {
                "title": "New Listing",
                "description": "New Description",
                "rent_per_hour": 15.0,
                "available_from": datetime.now().date(),
                "available_until": datetime.now().date(),
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
        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]),
            {
                "title": "Updated Listing",
                "description": "Updated Description",
                "rent_per_hour": 20.0,
                "available_from": datetime.now().date(),
                "available_until": datetime.now().date(),
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
