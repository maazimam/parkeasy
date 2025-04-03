from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from listings.forms import ListingForm
from listings.models import Listing, ListingSlot
from booking.models import Booking, BookingSlot

#############################
# Tests for views (listings/tests/test_views.py)
#############################


class ListingViewsTests(TestCase):
    def setUp(self):
        # Create a test user and log in.
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = Client()
        self.client.login(username="testuser", password="testpass")

        # Create a sample listing.
        self.listing = Listing.objects.create(
            user=self.user,
            title="Test Listing",
            location="Test Location [12.34, 56.78]",
            rent_per_hour=Decimal("10.00"),
            description="A test listing.",
            has_ev_charger=False,
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
        data = {
            f"{prefix}-TOTAL_FORMS": str(count),
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
        }
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
            "has_ev_charger": False,
            "charger_level": "",
            "connector_type": "",
        }
        slot_data = {
            "form-0-start_date": tomorrow.strftime("%Y-%m-%d"),
            "form-0-start_time": "09:00",
            "form-0-end_date": tomorrow.strftime("%Y-%m-%d"),
            "form-0-end_time": "17:00",
        }
        formset_data = self._build_slot_formset_data(
            prefix="form", count=1, slot_data=slot_data
        )
        post_data = {**listing_data, **formset_data}
        response = self.client.post(reverse("create_listing"), post_data)
        if response.status_code != 302:
            print("Listing form errors:", response.context["form"].errors)
            print("Slot formset errors:", response.context.get("slot_formset").errors)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("view_listings"))
        self.assertTrue(Listing.objects.filter(title="New Listing").exists())
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
            "has_ev_charger": False,
            "charger_level": "",
            "connector_type": "",
        }
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

    def test_edit_listing_pending_bookings(self):
        Booking.objects.create(
            user=self.user,
            listing=self.listing,
            email="pending@example.com",
            total_price=0,
            status="PENDING",
        )
        url = reverse("edit_listing", args=[self.listing.id])
        listing_data = {
            "title": "Attempted Edit",
            "description": "Attempt edit with pending booking",
            "rent_per_hour": "12.00",
            "location": self.listing.location,
            "has_ev_charger": False,
            "charger_level": "",
            "connector_type": "",
        }
        slot_data = self._build_slot_formset_data(prefix="form", count=1)
        post_data = {**listing_data, **slot_data}
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "You cannot edit your listing while there is a pending booking"
        )

    def test_edit_listing_active_booking_conflict(self):
        booking = Booking.objects.create(
            user=self.user,
            listing=self.listing,
            email="active@example.com",
            total_price=0,
            status="APPROVED",
        )
        BookingSlot.objects.create(
            booking=booking,
            start_date=self.listing.slots.first().start_date,
            start_time="10:00",
            end_date=self.listing.slots.first().start_date,
            end_time="12:00",
        )
        url = reverse("edit_listing", args=[self.listing.id])
        print(url)
        listing_data = {
            "title": "Conflict Edit",
            "description": "Conflicting interval",
            "rent_per_hour": "10.00",
            "location": self.listing.location,
            "has_ev_charger": False,
            "charger_level": "",
            "connector_type": "",
        }
        slot_data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-start_date": self.listing.slots.first().start_date.strftime(
                "%Y-%m-%d"
            ),
            "form-0-start_time": "11:00",
            "form-0-end_date": self.listing.slots.first().start_date.strftime(
                "%Y-%m-%d"
            ),
            "form-0-end_time": "13:00",
        }
        post_data = {**listing_data, **slot_data}
        response = self.client.post(
            reverse("edit_listing", args=[self.listing.id]), post_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "conflict with an active booking")

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

    def test_delete_listing_active_booking(self):
        Booking.objects.create(
            user=self.user,
            listing=self.listing,
            email="conflict@example.com",
            total_price=0,
            status="PENDING",
        )
        url = reverse("delete_listing", args=[self.listing.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cannot delete listing with pending bookings")

    def test_listing_reviews_view(self):
        url = reverse("listing_reviews", args=[self.listing.id])
        booking = Booking.objects.create(
            user=self.user,
            listing=self.listing,
            email="review@example.com",
            total_price=0,
            status="APPROVED",
        )
        from listings.models import Review

        Review.objects.create(
            booking=booking,
            listing=self.listing,
            user=self.user,
            rating=5,
            comment="Great!",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/listing_reviews.html")
        self.assertIn("reviews", response.context)


class ListingsFilterTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="filteruser", password="pass")
        self.client.login(username="filteruser", password="pass")
        # Set test_date to a future date.
        self.test_date = date.today() + timedelta(days=5)
        # Create Listing 1: Future Listing – available from test_date 09:00 to (test_date+5 days) 17:00.
        self.future_listing = Listing.objects.create(
            user=self.user,
            title="Future Listing",
            location="Future Location",
            rent_per_hour=10.00,
            description="Should be included",
        )
        ListingSlot.objects.create(
            listing=self.future_listing,
            start_date=self.test_date,
            start_time=time(9, 0),
            end_date=self.test_date + timedelta(days=5),
            end_time=time(17, 0),
        )
        # Listing 2: Today with future time – available on test_date 14:00 to 18:00.
        self.today_future = Listing.objects.create(
            user=self.user,
            title="Today Future Time",
            location="Today Location",
            rent_per_hour=10.00,
            description="Should be included",
        )
        ListingSlot.objects.create(
            listing=self.today_future,
            start_date=self.test_date,
            start_time=time(14, 0),
            end_date=self.test_date,
            end_time=time(18, 0),
        )
        # Listing 3: Today with past time – available on test_date 09:00 to 12:00.
        self.today_past = Listing.objects.create(
            user=self.user,
            title="Today Past Time",
            location="Past Location",
            rent_per_hour=10.00,
            description="Should be excluded",
        )
        ListingSlot.objects.create(
            listing=self.today_past,
            start_date=self.test_date,
            start_time=time(9, 0),
            end_date=self.test_date,
            end_time=time(12, 0),
        )

        # Patch datetime in listings.views so that "now" is before self.test_date.
        self.patcher = patch("listings.views.datetime")
        self.mock_datetime = self.patcher.start()
        fixed_now = datetime.combine(self.test_date - timedelta(days=1), time(12, 0))
        self.mock_datetime.now.return_value = fixed_now
        self.mock_datetime.combine = datetime.combine
        self.mock_datetime.strptime = datetime.strptime

    def tearDown(self):
        self.patcher.stop()

    def test_view_listings_default(self):
        url = reverse("view_listings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("listings", response.context)

    def test_view_listings_filter_max_price(self):
        Listing.objects.create(
            user=self.user,
            title="Expensive Listing",
            location="999 Rich St",
            rent_per_hour=50.00,
            description="Expensive",
        )
        url = reverse("view_listings")
        response = self.client.get(url, {"max_price": "20"})
        self.assertEqual(response.status_code, 200)
        listings = response.context["listings"]
        for listing in listings:
            self.assertLessEqual(float(listing.rent_per_hour), 20.0)

    def test_view_listings_ajax(self):
        url = reverse("view_listings")
        response = self.client.get(url, {"ajax": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/partials/listing_cards.html")

    def test_single_interval_filter(self):
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
        titles = [listing.title for listing in context_listings]
        self.assertIn("Future Listing", titles)
        self.assertIn("Today Future Time", titles)
        self.assertNotIn("Today Past Time", titles)

    def test_multiple_intervals_filter(self):
        multi_listing = Listing.objects.create(
            user=self.user,
            title="Multi Interval Listing",
            location="Multi Location",
            rent_per_hour=15.00,
            description="Multiple intervals",
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
        titles = [listing.title for listing in response.context["listings"]]
        self.assertIn("Multi Interval Listing", titles)
        params["start_time_2"] = "15:30"
        params["end_time_2"] = "16:30"
        response = self.client.get(url, params)
        titles = [listing.title for listing in response.context["listings"]]
        self.assertNotIn("Multi Interval Listing", titles)

    def test_recurring_filter_invalid_time(self):
        url = reverse("view_listings")
        params = {
            "filter_type": "recurring",
            "recurring_pattern": "daily",
            "recurring_start_date": self.test_date.strftime("%Y-%m-%d"),
            "recurring_end_date": self.test_date.strftime("%Y-%m-%d"),
            "recurring_start_time": "14:00",
            "recurring_end_time": "12:00",
        }
        response = self.client.get(url, params)
        self.assertIn(
            "Start time must be before end time unless overnight booking is selected",
            response.context["error_messages"],
        )


class ManageListingsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="manageowner", password="pass")
        self.client.login(username="manageowner", password="pass")
        self.listing1 = Listing.objects.create(
            user=self.owner,
            title="Manage Listing 1",
            location="Loc 1",
            rent_per_hour=10.00,
            description="Desc 1",
        )
        self.listing2 = Listing.objects.create(
            user=self.owner,
            title="Manage Listing 2",
            location="Loc 2",
            rent_per_hour=12.00,
            description="Desc 2",
        )
        Booking.objects.create(
            user=self.owner,
            listing=self.listing1,
            email="a@example.com",
            total_price=0,
            status="PENDING",
        )
        Booking.objects.create(
            user=self.owner,
            listing=self.listing2,
            email="b@example.com",
            total_price=0,
            status="APPROVED",
        )

    def test_manage_listings_view(self):
        url = reverse("manage_listings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("listings", response.context)
        for listing in response.context["listings"]:
            self.assertTrue(hasattr(listing, "pending_bookings"))
            self.assertTrue(hasattr(listing, "approved_bookings"))


class ListingOwnerBookingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.renter = User.objects.create_user(username="renter", password="pass")
        self.listing = Listing.objects.create(
            user=self.owner,
            title="Owner Parking",
            location="Owner Loc [12,34]",
            rent_per_hour=10.00,
            description="Owner description",
            has_ev_charger=False,
        )
        ListingSlot.objects.create(
            listing=self.listing,
            start_date=(datetime.now() + timedelta(days=1)).date(),
            start_time="09:00",
            end_date=(datetime.now() + timedelta(days=1)).date(),
            end_time="17:00",
        )

    def test_owner_sees_badge_not_book_button(self):
        self.client.login(username="owner", password="pass")
        url = reverse("view_listings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your listing")
        self.assertContains(response, 'class="badge bg-secondary"')
        book_url = reverse("book_listing", args=[self.listing.id])
        self.assertNotContains(response, f'href="{book_url}"')
        self.assertNotContains(response, "Book Now")

    def test_non_owner_sees_book_button(self):
        self.client.login(username="renter", password="pass")
        url = reverse("view_listings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Your listing")
        book_url = reverse("book_listing", args=[self.listing.id])
        self.assertContains(response, f'href="{book_url}"')
        self.assertContains(response, 'class="btn btn-primary')
        self.assertContains(response, "Book Now")


class EVChargerViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="evuser", password="evpass")
        self.client.login(username="evuser", password="evpass")
        self.non_ev = Listing.objects.create(
            user=self.user,
            title="Regular Parking",
            location="Regular Loc",
            rent_per_hour=Decimal("10.00"),
            description="No EV charger",
            has_ev_charger=False,
        )
        self.l2 = Listing.objects.create(
            user=self.user,
            title="Level 2 Charging",
            location="L2 Loc",
            rent_per_hour=Decimal("15.00"),
            description="Standard charger",
            has_ev_charger=True,
            charger_level="L2",
            connector_type="J1772",
        )
        self.l3 = Listing.objects.create(
            user=self.user,
            title="Fast Charging Tesla",
            location="Tesla Loc",
            rent_per_hour=Decimal("25.00"),
            description="DC Fast Charging",
            has_ev_charger=True,
            charger_level="L3",
            connector_type="TESLA",
        )
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        for listing in [self.non_ev, self.l2, self.l3]:
            ListingSlot.objects.create(
                listing=listing,
                start_date=tomorrow,
                start_time="09:00",
                end_date=tomorrow,
                end_time="17:00",
            )

    def test_filter_by_ev_charger_presence(self):
        response = self.client.get(reverse("view_listings"), {"has_ev_charger": "on"})
        listings = response.context["listings"]
        ids = [listing.id for listing in listings]
        self.assertIn(self.l2.id, ids)
        self.assertIn(self.l3.id, ids)
        self.assertNotIn(self.non_ev.id, ids)

    def test_filter_by_charger_level(self):
        response = self.client.get(
            reverse("view_listings"), {"has_ev_charger": "on", "charger_level": "L3"}
        )
        listings = response.context["listings"]
        ids = [listing.id for listing in listings]
        self.assertIn(self.l3.id, ids)
        self.assertNotIn(self.l2.id, ids)
        self.assertNotIn(self.non_ev.id, ids)

    def test_filter_by_connector_type(self):
        response = self.client.get(
            reverse("view_listings"),
            {"has_ev_charger": "on", "connector_type": "TESLA"},
        )
        listings = response.context["listings"]
        ids = [listing.id for listing in listings]
        self.assertIn(self.l3.id, ids)
        self.assertNotIn(self.l2.id, ids)
        self.assertNotIn(self.non_ev.id, ids)

    def test_combined_ev_filters(self):
        l3_j1772 = Listing.objects.create(
            user=self.user,
            title="L3 with J1772",
            location="L3 J1772 Loc",
            rent_per_hour=Decimal("20.00"),
            description="Fast charging with J1772",
            has_ev_charger=True,
            charger_level="L3",
            connector_type="J1772",
        )
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        ListingSlot.objects.create(
            listing=l3_j1772,
            start_date=tomorrow,
            start_time="09:00",
            end_date=tomorrow,
            end_time="17:00",
        )
        response = self.client.get(
            reverse("view_listings"),
            {
                "has_ev_charger": "on",
                "charger_level": "L3",
                "connector_type": "TESLA",
            },
        )
        listings = response.context["listings"]
        ids = [listing.id for listing in listings]
        self.assertIn(self.l3.id, ids)
        self.assertNotIn(self.l2.id, ids)
        self.assertNotIn(l3_j1772.id, ids)
        self.assertContains(response, "Level 3")
        self.assertContains(response, "Tesla")
        self.assertContains(response, "fa-charging-station")
        self.assertContains(response, "fa-plug")
