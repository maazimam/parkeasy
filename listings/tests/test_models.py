from django.test import TestCase
from django.contrib.auth.models import User
from ..models import Listing, Review
from booking.models import Booking
from datetime import date, time


class ListingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.listing = Listing.objects.create(
            user=self.user,
            title="Test Listing",
            location="123 Test St",
            rent_per_hour=10.00,
            description="Test description",
            available_from=date(2023, 1, 1),
            available_until=date(2023, 12, 31),
            available_time_from=time(8, 0),
            available_time_until=time(18, 0),
        )

    def test_listing_creation(self):
        self.assertEqual(self.listing.title, "Test Listing")
        self.assertEqual(self.listing.location, "123 Test St")
        self.assertEqual(self.listing.rent_per_hour, 10.00)
        self.assertEqual(self.listing.description, "Test description")
        self.assertEqual(self.listing.available_from, date(2023, 1, 1))
        self.assertEqual(self.listing.available_until, date(2023, 12, 31))
        self.assertEqual(self.listing.available_time_from, time(8, 0))
        self.assertEqual(self.listing.available_time_until, time(18, 0))

    def test_listing_str(self):
        self.assertEqual(str(self.listing), "Test Listing - 123 Test St")


class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.listing = Listing.objects.create(
            user=self.user,
            title="Test Listing",
            location="123 Test St",
            rent_per_hour=10.00,
            description="Test description",
            available_from=date(2023, 1, 1),
            available_until=date(2023, 12, 31),
            available_time_from=time(8, 0),
            available_time_until=time(18, 0),
        )
        self.booking = Booking.objects.create(
            user=self.user,
            listing=self.listing,
            booking_date=date(2023, 6, 15),  # Correct field name
            start_time=time(9, 0),
            end_time=time(10, 0),
            total_price=10.00,
        )
        self.review = Review.objects.create(
            booking=self.booking,
            listing=self.listing,
            user=self.user,
            rating=5,
            comment="Great place!",
        )

    def test_review_creation(self):
        self.assertEqual(self.review.booking, self.booking)
        self.assertEqual(self.review.listing, self.listing)
        self.assertEqual(self.review.user, self.user)
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.comment, "Great place!")

    def test_review_str(self):
        self.assertEqual(str(self.review), "Review for Test Listing by testuser")
