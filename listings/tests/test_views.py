from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import ListingForm
from ..models import Listing, ListingSlot
from ..utils import extract_coordinates, simplify_location


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

    def _build_slot_formset_data(self, prefix="form", count=1, slot_data=None):
        """
        Helper method to build valid formset data for ListingSlotFormSet.
        Optionally override default slot data.
        """
        data = {
            f"{prefix}-TOTAL_FORMS": str(count),
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
        }
        # For one slot form, use default values (can be overridden)
        if count >= 1:
            default_data = {
                f"{prefix}-0-start_date": "2025-03-12",
                f"{prefix}-0-start_time": "10:00",
                f"{prefix}-0-end_date": "2025-03-12",
                f"{prefix}-0-end_time": "12:00",
            }
            if slot_data:
                default_data.update(slot_data)
            data.update(default_data)
        return data

    def test_create_listing_get(self):
        url = reverse("create_listing")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/create_listing.html")
        self.assertIsInstance(response.context["form"], ListingForm)
        self.assertIn("slot_formset", response.context)

    def test_create_listing_view_post(self):
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        listing_data = {
            "title": "New Listing",
            "description": "New Description",
            "rent_per_hour": "15.00",
            "location": "New Location [123, 456]",
        }
        # Build slot formset data using tomorrow's date and desired times.
        slot_data = {
            "form-0-start_date": tomorrow.strftime("%Y-%m-%d"),
            "form-0-start_time": "09:00",
            "form-0-end_date": tomorrow.strftime("%Y-%m-%d"),
            "form-0-end_time": "17:00",
        }
        formset_data = self._build_slot_formset_data(
            prefix="form", count=1, slot_data=slot_data
        )
        # Note: Do not include non-existent fields such as available_from/available_until.
        post_data = {**listing_data, **formset_data}

        response = self.client.post(reverse("create_listing"), post_data)
        if response.status_code != 302:
            print("Listing form errors:", response.context["form"].errors)
            print("Slot formset errors:", response.context.get("slot_formset").errors)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("view_listings"))
        self.assertTrue(Listing.objects.filter(title="New Listing").exists())
        # Verify that the new listing has a slot with the correct start date and time.
        new_listing = Listing.objects.get(title="New Listing")
        slot = new_listing.slots.first()
        self.assertEqual(
            slot.start_date.strftime("%Y-%m-%d"), tomorrow.strftime("%Y-%m-%d")
        )
        self.assertEqual(slot.start_time.strftime("%H:%M"), "09:00")

    def test_edit_listing_view_get(self):
        url = reverse("edit_listing", args=[self.listing.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/edit_listing.html")
        self.assertIsInstance(response.context["form"], ListingForm)
        self.assertIn("slot_formset", response.context)

    def test_edit_listing_view_post(self):
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        listing_data = {
            "title": "Updated Listing",
            "description": "Updated Description",
            "rent_per_hour": "20.00",
            "location": "Updated Location [123, 456]",
        }
        # For editing, include the ID of the existing slot.
        slot = self.listing.slots.first()
        slot_data = {
            "form-0-id": str(slot.id),
            "form-0-start_date": tomorrow.strftime("%Y-%m-%d"),
            "form-0-start_time": "09:00",
            "form-0-end_date": tomorrow.strftime("%Y-%m-%d"),
            "form-0-end_time": "17:00",
        }
        formset_data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        }
        formset_data.update(slot_data)
        post_data = {**listing_data, **formset_data}
        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]), post_data
        )
        if response.status_code != 302:
            print("Listing form errors:", response.context["form"].errors)
            print("Slot formset errors:", response.context.get("slot_formset").errors)
        self.assertRedirects(response, reverse("manage_listings"))
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, "Updated Listing")
        updated_slot = self.listing.slots.first()
        self.assertEqual(
            updated_slot.start_date.strftime("%Y-%m-%d"), tomorrow.strftime("%Y-%m-%d")
        )
        self.assertEqual(updated_slot.start_time.strftime("%H:%M"), "09:00")

    def test_delete_listing_view_get(self):
        url = reverse("delete_listing", args=[self.listing.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/confirm_delete.html")

    def test_delete_listing_view_post(self):
        url = reverse("delete_listing", args=[self.listing.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("manage_listings"))
        self.assertFalse(Listing.objects.filter(id=self.listing.id).exists())

    def test_listing_reviews_view(self):
        url = reverse("listing_reviews", args=[self.listing.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/listing_reviews.html")
        self.assertIn("reviews", response.context)


class ListingsFilterTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        # Set a fixed test date for filtering
        self.test_date = date(2025, 3, 15)

        # Mock the current datetime to be 13:00 on test_date
        # This ensures our "future time" tests work consistently
        self.current_datetime = datetime.combine(self.test_date, time(13, 0))

        # Patch datetime.now() to return our fixed time
        from unittest.mock import patch

        self.datetime_patcher = patch("listings.views.datetime")
        self.mock_datetime = self.datetime_patcher.start()
        self.mock_datetime.now.return_value = self.current_datetime
        # Make sure strptime and combine still work
        self.mock_datetime.strptime = datetime.strptime
        self.mock_datetime.combine = datetime.combine

    def tearDown(self):
        # Stop patching datetime
        self.datetime_patcher.stop()

    def test_listing_time_filtering_single_interval(self):
        # Create listings with associated slots.

        # 1. Future Listing – slot from test_date 09:00 to (test_date+5 days) 17:00
        future_listing = Listing.objects.create(
            user=self.user,
            title="Future Listing",
            location="Future Location",
            rent_per_hour=10.0,
            description="This should be included",
        )
        ListingSlot.objects.create(
            listing=future_listing,
            start_date=self.test_date,
            start_time=time(9, 0),
            end_date=self.test_date + timedelta(days=5),
            end_time=time(17, 0),
        )

        # 2. Today with future time – slot from test_date 14:00 to 18:00
        today_future = Listing.objects.create(
            user=self.user,
            title="Today Future Time",
            location="Today Location",
            rent_per_hour=10.0,
            description="This should be included",
        )
        ListingSlot.objects.create(
            listing=today_future,
            start_date=self.test_date,
            start_time=time(14, 0),
            end_date=self.test_date,
            end_time=time(18, 0),
        )

        # 3. Today with past time – slot from test_date 09:00 to 12:00
        today_past = Listing.objects.create(
            user=self.user,
            title="Today Past Time",
            location="Today Past Location",
            rent_per_hour=10.0,
            description="This should be excluded",
        )
        ListingSlot.objects.create(
            listing=today_past,
            start_date=self.test_date,
            start_time=time(9, 0),
            end_date=self.test_date,
            end_time=time(12, 0),
        )

        # Apply single continuous interval filter
        url = reverse("view_listings")
        params = {
            "filter_type": "single",
            "start_date": self.test_date.strftime("%Y-%m-%d"),
            "end_date": self.test_date.strftime("%Y-%m-%d"),
            "start_time": "14:00",
            "end_time": "15:00",
        }
        response = self.client.get(url, params)
        context_listings = response.context["listings"]
        listing_titles = [listing.title for listing in context_listings]

        self.assertIn("Future Listing", listing_titles)
        self.assertIn("Today Future Time", listing_titles)
        self.assertNotIn("Today Past Time", listing_titles)
        self.assertEqual(len(listing_titles), 2)

    def test_listing_time_filtering_multiple_intervals(self):
        # Create a listing with two slots that together cover 10:00 to 16:00 on test_date.
        multi_listing = Listing.objects.create(
            user=self.user,
            title="Multi Interval Listing",
            location="Multi Location",
            rent_per_hour=15.0,
            description="This listing has multiple intervals",
        )
        ListingSlot.objects.create(
            listing=multi_listing,
            start_date=self.test_date,
            start_time=time(10, 0),
            end_date=self.test_date,
            end_time=time(13, 0),
        )
        ListingSlot.objects.create(
            listing=multi_listing,
            start_date=self.test_date,
            start_time=time(13, 0),
            end_date=self.test_date,
            end_time=time(16, 0),
        )

        url = reverse("view_listings")
        params = {
            "filter_type": "multiple",
            "interval_count": "2",
            "start_date_1": self.test_date.strftime("%Y-%m-%d"),
            "end_date_1": self.test_date.strftime("%Y-%m-%d"),
            "start_time_1": "10:00",
            "end_time_1": "12:00",
            "start_date_2": self.test_date.strftime("%Y-%m-%d"),
            "end_date_2": self.test_date.strftime("%Y-%m-%d"),
            "start_time_2": "14:00",
            "end_time_2": "15:00",
        }
        response = self.client.get(url, params)
        context_listings = response.context["listings"]
        listing_titles = [listing.title for listing in context_listings]
        # Listing should cover both intervals.
        self.assertIn("Multi Interval Listing", listing_titles)

        # Now change the second interval so it is not covered.
        params["start_time_2"] = "15:30"
        params["end_time_2"] = "16:30"
        response = self.client.get(url, params)
        context_listings = response.context["listings"]
        listing_titles = [listing.title for listing in context_listings]
        self.assertNotIn("Multi Interval Listing", listing_titles)


class ListingOwnerBookingTest(TestCase):
    def setUp(self):
        # Create two users: owner and non-owner.
        self.owner = User.objects.create_user(username="owner", password="ownerpass123")
        self.non_owner = User.objects.create_user(
            username="renter", password="renterpass123"
        )

        # Create a listing owned by the owner.
        self.listing = Listing.objects.create(
            user=self.owner,
            title="Test Parking Spot",
            location="Test Location [123.456, 789.012]",
            rent_per_hour=10.0,
            description="Test Description",
        )
        # Create a slot for the listing.
        ListingSlot.objects.create(
            listing=self.listing,
            start_date=(datetime.now() - timedelta(days=1)).date(),
            start_time=time(9, 0),
            end_date=(datetime.now() + timedelta(days=30)).date(),
            end_time=time(17, 0),
        )
        self.view_listings_url = reverse("view_listings")

    def test_owner_sees_badge_not_book_button(self):
        """Owners should see a badge (not a 'Book Now' button)."""
        self.client.login(username="owner", password="ownerpass123")
        response = self.client.get(self.view_listings_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your listing")
        self.assertContains(response, 'class="badge bg-secondary"')
        book_url = reverse("book_listing", args=[self.listing.id])
        self.assertNotContains(response, f'href="{book_url}"')
        self.assertNotContains(response, "Book Now")

    def test_non_owner_sees_book_button(self):
        """Non-owners should see the 'Book Now' button."""
        self.client.login(username="renter", password="renterpass123")
        response = self.client.get(self.view_listings_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Your listing")
        book_url = reverse("book_listing", args=[self.listing.id])
        self.assertContains(response, f'href="{book_url}"')
        self.assertContains(response, 'class="btn btn-primary')
        self.assertContains(response, "Book Now")


class SimplifyLocationTest(TestCase):
    def test_simplify_location_with_institution(self):
        # For educational institutions, the full building name is retained.
        loc = (
            "Tandon School of Engineering, Johnson Street, Downtown Brooklyn, Brooklyn"
        )
        simplified = simplify_location(loc)
        self.assertEqual(simplified, "Tandon School of Engineering, Brooklyn")

    def test_simplify_location_non_institution(self):
        # For non-institution addresses, the first two parts plus the city are used.
        loc = "Some Building, Some Street, Manhattan, Extra Info"
        simplified = simplify_location(loc)
        self.assertEqual(simplified, "Some Building, Some Street, Manhattan")

    def test_simplify_location_empty(self):
        simplified = simplify_location("")
        self.assertEqual(simplified, "")


class RecurringFilterTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        # Set a fixed test date for filtering
        self.test_date = date(2025, 3, 15)  # A Saturday

    # def test_daily_recurring_filter(self):
    #     # Create a listing available every day for a week
    #     daily_listing = Listing.objects.create(
    #         user=self.user,
    #         title="Daily Available Listing",
    #         location="Daily Location",
    #         rent_per_hour=15.0,
    #         description="Available every day from 10:00-14:00",
    #     )

    #     # Create slots for 5 consecutive days
    #     for i in range(5):
    #         current_date = self.test_date + timedelta(days=i)
    #         ListingSlot.objects.create(
    #             listing=daily_listing,
    #             start_date=current_date,
    #             start_time=time(10, 0),
    #             end_date=current_date,
    #             end_time=time(14, 0),
    #         )

    #     # Create another listing with gaps in availability
    #     partial_listing = Listing.objects.create(
    #         user=self.user,
    #         title="Partial Available Listing",
    #         location="Partial Location",
    #         rent_per_hour=20.0,
    #         description="Not available every day",
    #     )

    #     # Create slots for days 0, 2, 4 (skipping days 1 and 3)
    #     for i in range(0, 5, 2):
    #         current_date = self.test_date + timedelta(days=i)
    #         ListingSlot.objects.create(
    #             listing=partial_listing,
    #             start_date=current_date,
    #             start_time=time(10, 0),
    #             end_date=current_date,
    #             end_time=time(14, 0),
    #         )

    #     # Apply daily recurring filter for 3 consecutive days
    #     url = reverse("view_listings")
    #     params = {
    #         "filter_type": "recurring",
    #         "recurring_pattern": "daily",
    #         "recurring_start_date": self.test_date.strftime("%Y-%m-%d"),
    #         "recurring_end_date": (self.test_date + timedelta(days=2)).strftime(
    #             "%Y-%m-%d"
    #         ),
    #         "recurring_start_time": "11:00",
    #         "recurring_end_time": "13:00",
    #     }

    #     response = self.client.get(url, params)
    #     context_listings = response.context["listings"]
    #     listing_titles = [listing.title for listing in context_listings]

    #     # Daily listing should be included, partial listing should be excluded
    #     self.assertIn("Daily Available Listing", listing_titles)
    #     self.assertNotIn("Partial Available Listing", listing_titles)

    def test_weekly_recurring_filter(self):
        # Create a listing available same day every week
        weekly_listing = Listing.objects.create(
            user=self.user,
            title="Weekly Available Listing",
            location="Weekly Location",
            rent_per_hour=25.0,
            description="Available every Saturday",
        )

        # Create slots for 4 consecutive Saturdays
        for i in range(0, 28, 7):  # 0, 7, 14, 21 - four Saturdays
            current_date = self.test_date + timedelta(days=i)
            ListingSlot.objects.create(
                listing=weekly_listing,
                start_date=current_date,
                start_time=time(9, 0),
                end_date=current_date,
                end_time=time(17, 0),
            )

        # Create another listing with inconsistent weekly availability
        inconsistent_listing = Listing.objects.create(
            user=self.user,
            title="Inconsistent Weekly Listing",
            location="Inconsistent Location",
            rent_per_hour=30.0,
            description="Missing some Saturdays",
        )

        # Create slots for 1st and 3rd Saturdays only (missing 2nd and 4th)
        for i in range(0, 28, 14):  # 0, 14 - two Saturdays
            current_date = self.test_date + timedelta(days=i)
            ListingSlot.objects.create(
                listing=inconsistent_listing,
                start_date=current_date,
                start_time=time(9, 0),
                end_date=current_date,
                end_time=time(17, 0),
            )

            # NEW: Create a listing available every week but at wrong time
        wrong_time_listing = Listing.objects.create(
            user=self.user,
            title="Wrong Time Weekly Listing",
            location="Wrong Time Location",
            rent_per_hour=35.0,
            description="Available every Saturday but outside requested hours",
        )

        # Create slots for 4 consecutive Saturdays but only from 6-8am and 18-20pm
        for i in range(0, 28, 7):
            current_date = self.test_date + timedelta(days=i)
            # Morning slot (too early)
            ListingSlot.objects.create(
                listing=wrong_time_listing,
                start_date=current_date,
                start_time=time(6, 0),
                end_date=current_date,
                end_time=time(8, 0),
            )
            # Evening slot (too late)
            ListingSlot.objects.create(
                listing=wrong_time_listing,
                start_date=current_date,
                start_time=time(18, 0),
                end_date=current_date,
                end_time=time(20, 0),
            )

        # Apply weekly recurring filter for 3 weeks
        url = reverse("view_listings")
        params = {
            "filter_type": "recurring",
            "recurring_pattern": "weekly",
            "recurring_start_date": self.test_date.strftime("%Y-%m-%d"),
            "recurring_weeks": "3",
            "recurring_start_time": "10:00",
            "recurring_end_time": "16:00",
        }

        response = self.client.get(url, params)
        context_listings = response.context["listings"]
        listing_titles = [listing.title for listing in context_listings]

        # Weekly listing should be included
        self.assertIn("Weekly Available Listing", listing_titles)

        # Both inconsistent pattern and wrong time listings should be excluded
        self.assertNotIn("Inconsistent Weekly Listing", listing_titles)
        self.assertNotIn("Wrong Time Weekly Listing", listing_titles)

    # def test_overnight_recurring_filter(self):
    #     # Create a listing available for overnight stays (24/7)
    #     overnight_listing = Listing.objects.create(
    #         user=self.user,
    #         title="Overnight Listing",
    #         location="Overnight Location",
    #         rent_per_hour=40.0,
    #         description="Available for overnight stays",
    #     )

    #     # Create slots for 3 consecutive days (to cover 2 nights)
    #     for i in range(3):
    #         current_date = self.test_date + timedelta(days=i)
    #         ListingSlot.objects.create(
    #             listing=overnight_listing,
    #             start_date=current_date,
    #             start_time=time(0, 0),  # Available all day
    #             end_date=current_date,
    #             end_time=time(23, 59),
    #         )

    #     # Create a listing that's only available during daytime hours
    #     daytime_listing = Listing.objects.create(
    #         user=self.user,
    #         title="Daytime Only Listing",
    #         location="Daytime Location",
    #         rent_per_hour=30.0,
    #         description="Only available during daytime hours",
    #     )

    #     # Create daytime-only slots for the same 3 consecutive days
    #     for i in range(3):
    #         current_date = self.test_date + timedelta(days=i)
    #         ListingSlot.objects.create(
    #             listing=daytime_listing,
    #             start_date=current_date,
    #             start_time=time(9, 0),  # Available from 9am
    #             end_date=current_date,
    #             end_time=time(17, 0),  # Until 5pm
    #         )

    #     # Apply overnight recurring filter
    #     url = reverse("view_listings")
    #     params = {
    #         "filter_type": "recurring",
    #         "recurring_pattern": "daily",
    #         "recurring_start_date": self.test_date.strftime("%Y-%m-%d"),
    #         "recurring_end_date": (self.test_date + timedelta(days=1)).strftime(
    #             "%Y-%m-%d"
    #         ),
    #         "recurring_start_time": "22:00",
    #         "recurring_end_time": "08:00",  # End time is before start time, requiring overnight
    #         "recurring_overnight": "on",
    #     }

    #     response = self.client.get(url, params)
    #     context_listings = response.context["listings"]
    #     listing_titles = [listing.title for listing in context_listings]

    #     # Overnight listing should be included
    #     self.assertIn("Overnight Listing", listing_titles)
    #     # Daytime-only listing should NOT be included
    #     self.assertNotIn("Daytime Only Listing", listing_titles)

    def test_start_time_after_end_time_validation(self):
        # Apply filter with start time after end time without overnight option
        url = reverse("view_listings")
        params = {
            "filter_type": "recurring",
            "recurring_pattern": "daily",
            "recurring_start_date": self.test_date.strftime("%Y-%m-%d"),
            "recurring_end_date": self.test_date.strftime("%Y-%m-%d"),
            "recurring_start_time": "14:00",
            "recurring_end_time": "12:00",  # End time before start time
        }

        response = self.client.get(url, params)

        # Should get an error message
        self.assertIn(
            "Start time must be before end time unless overnight booking is selected",
            response.context["error_messages"],
        )


class EVChargerViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="evuser", password="evpassword")
        self.client.login(username="evuser", password="evpassword")

        # Create a non-EV listing
        self.non_ev_listing = Listing.objects.create(
            user=self.user,
            title="Regular Parking",
            location="Regular Location",
            rent_per_hour=Decimal("10.00"),
            description="No EV charger here",
            has_ev_charger=False,
        )

        # Create an L2 J1772 listing
        self.l2_listing = Listing.objects.create(
            user=self.user,
            title="Level 2 Charging",
            location="L2 Location",
            rent_per_hour=Decimal("15.00"),
            description="Standard Level 2 charger",
            has_ev_charger=True,
            charger_level="L2",
            connector_type="J1772",
        )

        # Create an L3 Tesla listing
        self.l3_listing = Listing.objects.create(
            user=self.user,
            title="Fast Charging Tesla",
            location="Tesla Location",
            rent_per_hour=Decimal("25.00"),
            description="DC Fast Charging for Tesla",
            has_ev_charger=True,
            charger_level="L3",
            connector_type="TESLA",
        )

        # Create slots for all listings to ensure they appear in searches
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        for listing in [self.non_ev_listing, self.l2_listing, self.l3_listing]:
            ListingSlot.objects.create(
                listing=listing,
                start_date=tomorrow,
                start_time="09:00",
                end_date=tomorrow,
                end_time="17:00",
            )

    def test_create_listing_with_ev_charger(self):
        """Test creating a new listing with EV charger information"""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        listing_data = {
            "title": "New EV Listing",
            "description": "New EV Description",
            "rent_per_hour": "20.00",
            "location": "New EV Location [123, 456]",
            "has_ev_charger": "on",  # Checkbox value when checked
            "charger_level": "L1",
            "connector_type": "CHAdeMO",
        }

        # Add slot formset data
        slot_data = {
            "form-0-start_date": tomorrow.strftime("%Y-%m-%d"),
            "form-0-start_time": "09:00",
            "form-0-end_date": tomorrow.strftime("%Y-%m-%d"),
            "form-0-end_time": "17:00",
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        }

        post_data = {**listing_data, **slot_data}
        response = self.client.post(reverse("create_listing"), post_data)

        # Check redirect indicates success
        self.assertEqual(response.status_code, 302)

        # Verify listing was created with correct EV data
        new_listing = Listing.objects.get(title="New EV Listing")
        self.assertTrue(new_listing.has_ev_charger)
        self.assertEqual(new_listing.charger_level, "L1")
        self.assertEqual(new_listing.connector_type, "CHAdeMO")

    def test_edit_listing_add_ev_charger(self):
        """Test editing a non-EV listing to add EV charger information"""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        listing_data = {
            "title": "Updated with EV",
            "description": "Now with EV charger",
            "rent_per_hour": "15.00",
            "location": self.non_ev_listing.location,
            "has_ev_charger": "on",
            "charger_level": "L2",
            "connector_type": "CCS",
        }

        # Add slot formset data for the existing slot
        slot = self.non_ev_listing.slots.first()
        slot_data = {
            "form-0-id": str(slot.id),
            "form-0-start_date": tomorrow.strftime("%Y-%m-%d"),
            "form-0-start_time": "09:00",
            "form-0-end_date": tomorrow.strftime("%Y-%m-%d"),
            "form-0-end_time": "17:00",
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        }

        post_data = {**listing_data, **slot_data}
        response = self.client.post(
            reverse("edit_listing", args=[self.non_ev_listing.id]), post_data
        )

        # Check redirect indicates success
        self.assertEqual(response.status_code, 302)

        # Verify listing was updated with EV data
        self.non_ev_listing.refresh_from_db()
        self.assertTrue(self.non_ev_listing.has_ev_charger)
        self.assertEqual(self.non_ev_listing.charger_level, "L2")
        self.assertEqual(self.non_ev_listing.connector_type, "CCS")

    def test_edit_listing_remove_ev_charger(self):
        """Test editing an EV listing to remove EV charger information"""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        listing_data = {
            "title": "No Longer EV",
            "description": "Removed EV charger",
            "rent_per_hour": "10.00",
            "location": self.l2_listing.location,
        }

        # Add slot formset data for the existing slot
        slot = self.l2_listing.slots.first()
        slot_data = {
            "form-0-id": str(slot.id),
            "form-0-start_date": tomorrow.strftime("%Y-%m-%d"),
            "form-0-start_time": "09:00",
            "form-0-end_date": tomorrow.strftime("%Y-%m-%d"),
            "form-0-end_time": "17:00",
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        }

        post_data = {**listing_data, **slot_data}
        response = self.client.post(
            reverse("edit_listing", args=[self.l2_listing.id]), post_data
        )

        # Check redirect indicates success
        self.assertEqual(response.status_code, 302)

        # Verify listing was updated with EV charger removed
        self.l2_listing.refresh_from_db()
        self.assertFalse(self.l2_listing.has_ev_charger)
        self.assertEqual(self.l2_listing.charger_level, "")  # Should be cleared
        self.assertEqual(self.l2_listing.connector_type, "")  # Should be cleared

    def test_filter_by_ev_charger_presence(self):
        """Test filtering listings by presence of EV charger"""
        response = self.client.get(reverse("view_listings"), {"has_ev_charger": "on"})

        # Check that filtering works
        listings = response.context["listings"]
        listing_ids = [listing.id for listing in listings]

        # Should include both EV listings
        self.assertIn(self.l2_listing.id, listing_ids)
        self.assertIn(self.l3_listing.id, listing_ids)

        # Should exclude non-EV listing
        self.assertNotIn(self.non_ev_listing.id, listing_ids)

    def test_filter_by_charger_level(self):
        """Test filtering listings by specific charger level"""
        response = self.client.get(
            reverse("view_listings"), {"has_ev_charger": "on", "charger_level": "L3"}
        )

        listings = response.context["listings"]
        listing_ids = [listing.id for listing in listings]

        # Should include only L3 listing
        self.assertIn(self.l3_listing.id, listing_ids)

        # Should exclude L2 listing
        self.assertNotIn(self.l2_listing.id, listing_ids)

        # Should exclude non-EV listing
        self.assertNotIn(self.non_ev_listing.id, listing_ids)

    def test_filter_by_connector_type(self):
        """Test filtering listings by specific connector type"""
        response = self.client.get(
            reverse("view_listings"),
            {"has_ev_charger": "on", "connector_type": "TESLA"},
        )

        listings = response.context["listings"]
        listing_ids = [listing.id for listing in listings]

        # Should include only Tesla listing
        self.assertIn(self.l3_listing.id, listing_ids)

        # Should exclude J1772 listing
        self.assertNotIn(self.l2_listing.id, listing_ids)

        # Should exclude non-EV listing
        self.assertNotIn(self.non_ev_listing.id, listing_ids)

    def test_combined_ev_filters(self):
        """Test combining multiple EV filter criteria"""
        # Create an L3 J1772 listing to test combined filters
        l3_j1772_listing = Listing.objects.create(
            user=self.user,
            title="L3 with J1772",
            location="L3 J1772 Location",
            rent_per_hour=Decimal("20.00"),
            description="Fast charging with J1772",
            has_ev_charger=True,
            charger_level="L3",
            connector_type="J1772",
        )

        # Add slots to make it appear in searches
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        ListingSlot.objects.create(
            listing=l3_j1772_listing,
            start_date=tomorrow,
            start_time="09:00",
            end_date=tomorrow,
            end_time="17:00",
        )

        # Filter for L3 + TESLA
        response = self.client.get(
            reverse("view_listings"),
            {"has_ev_charger": "on", "charger_level": "L3", "connector_type": "TESLA"},
        )

        listings = response.context["listings"]
        listing_ids = [listing.id for listing in listings]

        # Should include only L3 Tesla listing
        self.assertIn(self.l3_listing.id, listing_ids)

        # Should exclude L2 J1772 listing
        self.assertNotIn(self.l2_listing.id, listing_ids)

        # Should exclude L3 J1772 listing
        self.assertNotIn(l3_j1772_listing.id, listing_ids)

    def test_ev_badge_displayed(self):
        """Test that listings with EV chargers show the EV badge in the view"""
        response = self.client.get(reverse("view_listings"))

        # Check that EV charger details appear for L2 listing
        self.assertContains(response, "Level 2")
        self.assertContains(response, "J1772")

        # Check that EV charger details appear for L3 listing
        self.assertContains(response, "Level 3")
        self.assertContains(response, "Tesla")

        # Check badge formatting
        self.assertContains(response, "fa-charging-station")
        self.assertContains(response, "fa-plug")


class LocationSearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create test listings with different locations
        self.listing1 = Listing.objects.create(
            user=self.user,
            title="NYC Parking",
            location="[40.7128,-74.0060]",  # New York City coordinates
            rent_per_hour=Decimal("25.00"),
            description="Parking in NYC"
        )

        self.listing2 = Listing.objects.create(
            user=self.user,
            title="Boston Parking",
            location="[42.3601,-71.0589]",  # Boston coordinates
            rent_per_hour=Decimal("20.00"),
            description="Parking in Boston"
        )

        self.listing3 = Listing.objects.create(
            user=self.user,
            title="Invalid Location",
            location="invalid",
            rent_per_hour=Decimal("15.00"),
            description="Invalid location"
        )

        # Add slots to make listings appear in searches
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        for listing in [self.listing1, self.listing2, self.listing3]:
            ListingSlot.objects.create(
                listing=listing,
                start_date=tomorrow,
                start_time="09:00",
                end_date=tomorrow,
                end_time="17:00"
            )

    def test_location_search_with_radius(self):
        """Test searching listings within a specific radius"""
        # Search near NYC with 100km radius
        response = self.client.get(
            reverse('view_listings'),
            {'lat': '40.7128', 'lng': '-74.0060', 'radius': '100', 'enable_radius': 'on'}
        )

        self.assertEqual(response.status_code, 200)
        listings = list(response.context['listings'])

        # Get listings with valid distances within radius
        valid_listings = []
        for listing in listings:
            if hasattr(listing, 'distance') and listing.distance is not None:
                if listing.distance <= 100:
                    valid_listings.append(listing)

        # Only NYC listing should be within 100km
        self.assertEqual(len(valid_listings), 1)
        self.assertEqual(valid_listings[0].title, "NYC Parking")
        self.assertLess(valid_listings[0].distance, 1)  # NYC listing should be very close

    def test_location_search_without_radius(self):
        """Test searching listings without radius (should sort by distance)"""
        response = self.client.get(
            reverse('view_listings'),
            {'lat': '40.7128', 'lng': '-74.0060'}
        )

        self.assertEqual(response.status_code, 200)
        listings = list(response.context['listings'])
        # All listings should be included, but sorted by distance
        self.assertEqual(len(listings), 3)  # Including the invalid location listing

        # Check that listings with valid coordinates have distances
        valid_listings = [l for l in listings if hasattr(l, 'distance') and l.distance is not None]
        self.assertEqual(len(valid_listings), 2)

        # NYC should be first among valid listings (closest)
        self.assertEqual(valid_listings[0].title, "NYC Parking")

    def test_distance_calculation(self):
        """Test that distances are correctly calculated and added to listings"""
        response = self.client.get(
            reverse('view_listings'),
            {'lat': '40.7128', 'lng': '-74.0060'}
        )

        self.assertEqual(response.status_code, 200)
        listings = list(response.context['listings'])
        nyc_listing = next(l for l in listings if l.title == "NYC Parking")

        # NYC listing should have distance close to 0
        self.assertTrue(hasattr(nyc_listing, 'distance'))
        self.assertLess(nyc_listing.distance, 1)

    def test_coordinate_extraction(self):
        """Test the coordinate extraction utility function"""
        # Test valid coordinates
        lat, lng = extract_coordinates("[40.7128,-74.0060]")
        self.assertAlmostEqual(lat, 40.7128)
        self.assertAlmostEqual(lng, -74.0060)

        # Test invalid coordinates
        with self.assertRaises(ValueError):
            extract_coordinates("invalid")

    def test_listings_without_coordinates(self):
        """Test that listings with invalid coordinates are still included"""
        response = self.client.get(
            reverse('view_listings'),
            {'lat': '40.7128', 'lng': '-74.0060'}
        )

        self.assertEqual(response.status_code, 200)
        invalid_listing = next(
            (listing for listing in response.context['listings']
             if listing.title == "Invalid Location"),
            None
        )
        # Invalid listing should be included with None distance
        self.assertIsNotNone(invalid_listing)
        self.assertIsNone(invalid_listing.distance)
