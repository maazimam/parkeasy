from django.test import TestCase
from django.contrib.auth.models import User
from listings.models import Listing, ListingSlot
import datetime as dt
from decimal import Decimal


class ListingModelTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

        # Create test listing
        self.listing = Listing.objects.create(
            user=self.user,
            title="Test Space",
            location="123 Test Street, Test City",
            rent_per_hour=Decimal("25.50"),
            description="A test space for testing purposes",
        )

    def test_listing_creation(self):
        """Test the creation of a listing with all required fields."""
        self.assertEqual(self.listing.title, "Test Space")
        self.assertEqual(self.listing.location, "123 Test Street, Test City")
        self.assertEqual(self.listing.rent_per_hour, Decimal("25.50"))
        self.assertEqual(self.listing.description, "A test space for testing purposes")
        self.assertEqual(self.listing.user, self.user)
        self.assertIsNotNone(self.listing.created_at)
        self.assertIsNotNone(self.listing.updated_at)

    def test_string_representation(self):
        """Test the string representation of a Listing."""
        expected_string = "Test Space - 123 Test Street, Test City"
        self.assertEqual(str(self.listing), expected_string)

    def test_average_rating_no_reviews(self):
        """Test average_rating returns None when there are no reviews."""
        self.assertIsNone(self.listing.avg_rating)

    def test_is_available_for_range_single_slot(self):
        """Test availability check with a single slot covering the entire range."""
        # Create a slot for today 9am-5pm
        today = dt.date.today()
        slot = ListingSlot.objects.create(
            listing=self.listing,
            start_date=today,
            start_time=dt.time(9, 0),
            end_date=today,
            end_time=dt.time(17, 0),
        )
        print(slot)
        # Test range within the slot (10am-3pm)
        start_dt = dt.datetime.combine(today, dt.time(10, 0))
        end_dt = dt.datetime.combine(today, dt.time(15, 0))
        self.assertTrue(self.listing.is_available_for_range(start_dt, end_dt))

        # Test range outside the slot (6pm-8pm)
        start_dt = dt.datetime.combine(today, dt.time(18, 0))
        end_dt = dt.datetime.combine(today, dt.time(20, 0))
        self.assertFalse(self.listing.is_available_for_range(start_dt, end_dt))

    def test_is_available_for_range_multiple_slots(self):
        """Test availability with multiple slots that together cover the range."""
        today = dt.date.today()
        tomorrow = today + dt.timedelta(days=1)

        # Create two consecutive slots
        ListingSlot.objects.create(
            listing=self.listing,
            start_date=today,
            start_time=dt.time(9, 0),
            end_date=today,
            end_time=dt.time(17, 0),
        )

        ListingSlot.objects.create(
            listing=self.listing,
            start_date=tomorrow,
            start_time=dt.time(9, 0),
            end_date=tomorrow,
            end_time=dt.time(17, 0),
        )

        # Test range across both slots
        start_dt = dt.datetime.combine(today, dt.time(14, 0))
        end_dt = dt.datetime.combine(tomorrow, dt.time(12, 0))
        self.assertFalse(self.listing.is_available_for_range(start_dt, end_dt))

        # Create a continuous slot bridging the gap
        ListingSlot.objects.create(
            listing=self.listing,
            start_date=today,
            start_time=dt.time(17, 0),
            end_date=tomorrow,
            end_time=dt.time(9, 0),
        )

        # Now the range should be covered
        self.assertTrue(self.listing.is_available_for_range(start_dt, end_dt))

    def test_is_available_for_range_with_gap(self):
        """Test availability with multiple slots that have a gap between them."""
        today = dt.date.today()

        # Create two slots with a gap between them
        ListingSlot.objects.create(
            listing=self.listing,
            start_date=today,
            start_time=dt.time(9, 0),
            end_date=today,
            end_time=dt.time(12, 0),
        )

        ListingSlot.objects.create(
            listing=self.listing,
            start_date=today,
            start_time=dt.time(14, 0),
            end_date=today,
            end_time=dt.time(17, 0),
        )

        # Test range that spans the gap
        start_dt = dt.datetime.combine(today, dt.time(11, 0))
        end_dt = dt.datetime.combine(today, dt.time(15, 0))
        self.assertFalse(self.listing.is_available_for_range(start_dt, end_dt))

    def test_is_available_for_range_exact_match(self):
        """Test availability when request exactly matches a slot."""
        today = dt.date.today()

        ListingSlot.objects.create(
            listing=self.listing,
            start_date=today,
            start_time=dt.time(9, 0),
            end_date=today,
            end_time=dt.time(17, 0),
        )

        # Exact match of the slot
        start_dt = dt.datetime.combine(today, dt.time(9, 0))
        end_dt = dt.datetime.combine(today, dt.time(17, 0))
        self.assertTrue(self.listing.is_available_for_range(start_dt, end_dt))

    def test_earliest_start_datetime_no_slots(self):
        """Test earliest_start_datetime returns None when there are no slots."""
        # Make sure self.listing has no slots
        ListingSlot.objects.filter(listing=self.listing).delete()
        self.assertIsNone(self.listing.earliest_start_datetime)

    def test_latest_end_datetime_no_slots(self):
        """Test latest_end_datetime returns None when there are no slots."""
        # Make sure self.listing has no slots
        ListingSlot.objects.filter(listing=self.listing).delete()
        self.assertIsNone(self.listing.latest_end_datetime)

    def test_earliest_start_datetime_single_slot(self):
        """Test earliest_start_datetime for a listing with a single slot."""
        # Clear any existing slots
        ListingSlot.objects.filter(listing=self.listing).delete()

        today = dt.date.today()
        slot_time = dt.time(9, 30)

        # Create a slot
        ListingSlot.objects.create(
            listing=self.listing,
            start_date=today,
            start_time=slot_time,
            end_date=today,
            end_time=dt.time(17, 0),
        )

        expected_datetime = dt.datetime.combine(today, slot_time)
        self.assertEqual(self.listing.earliest_start_datetime, expected_datetime)

    def test_latest_end_datetime_single_slot(self):
        """Test latest_end_datetime for a listing with a single slot."""
        # Clear any existing slots
        ListingSlot.objects.filter(listing=self.listing).delete()

        today = dt.date.today()
        slot_time = dt.time(17, 30)

        # Create a slot
        ListingSlot.objects.create(
            listing=self.listing,
            start_date=today,
            start_time=dt.time(9, 0),
            end_date=today,
            end_time=slot_time,
        )

        expected_datetime = dt.datetime.combine(today, slot_time)
        self.assertEqual(self.listing.latest_end_datetime, expected_datetime)

    def test_earliest_start_datetime_multiple_dates(self):
        """Test earliest_start_datetime with slots on different dates."""
        # Clear any existing slots
        ListingSlot.objects.filter(listing=self.listing).delete()

        today = dt.date.today()
        yesterday = today - dt.timedelta(days=1)

        # Create slots on different dates
        ListingSlot.objects.create(
            listing=self.listing,
            start_date=today,
            start_time=dt.time(9, 0),
            end_date=today,
            end_time=dt.time(17, 0),
        )
        ListingSlot.objects.create(
            listing=self.listing,
            start_date=yesterday,
            start_time=dt.time(8, 0),
            end_date=yesterday,
            end_time=dt.time(16, 0),
        )

        expected_datetime = dt.datetime.combine(yesterday, dt.time(8, 0))
        self.assertEqual(self.listing.earliest_start_datetime, expected_datetime)

    def test_latest_end_datetime_multiple_dates(self):
        """Test latest_end_datetime with slots on different dates."""
        # Clear any existing slots
        ListingSlot.objects.filter(listing=self.listing).delete()

        today = dt.date.today()
        tomorrow = today + dt.timedelta(days=1)

        # Create slots on different dates
        ListingSlot.objects.create(
            listing=self.listing,
            start_date=today,
            start_time=dt.time(9, 0),
            end_date=today,
            end_time=dt.time(17, 0),
        )
        ListingSlot.objects.create(
            listing=self.listing,
            start_date=tomorrow,
            start_time=dt.time(10, 0),
            end_date=tomorrow,
            end_time=dt.time(18, 0),
        )

        expected_datetime = dt.datetime.combine(tomorrow, dt.time(18, 0))
        self.assertEqual(self.listing.latest_end_datetime, expected_datetime)

    def test_ev_charger_default_values(self):
        """Test that EV charger fields have correct default values."""
        # Create a new listing without specifying EV charger fields
        new_listing = Listing.objects.create(
            user=self.user,
            title="EV Test Space",
            location="456 EV Street",
            rent_per_hour=Decimal("30.00"),
            description="A space for testing EV defaults",
        )

        # Check default values
        self.assertFalse(new_listing.has_ev_charger)
        self.assertEqual(new_listing.charger_level, "L2")  # Default is L2
        self.assertEqual(new_listing.connector_type, "J1772")  # Default is J1772

    def test_ev_charger_custom_values(self):
        """Test creating a listing with custom EV charger values."""
        ev_listing = Listing.objects.create(
            user=self.user,
            title="Tesla Charging Spot",
            location="789 Tesla Ave",
            rent_per_hour=Decimal("35.00"),
            description="A spot with Tesla charger",
            has_ev_charger=True,
            charger_level="L3",
            connector_type="TESLA",
        )

        # Check custom values were saved
        self.assertTrue(ev_listing.has_ev_charger)
        self.assertEqual(ev_listing.charger_level, "L3")
        self.assertEqual(ev_listing.connector_type, "TESLA")

    def test_ev_charger_display_values(self):
        """Test that the get_charger_level_display and get_connector_type_display methods work correctly."""
        ev_listing = Listing.objects.create(
            user=self.user,
            title="CCS Charging Spot",
            location="101 CCS Blvd",
            rent_per_hour=Decimal("40.00"),
            description="A spot with CCS fast charger",
            has_ev_charger=True,
            charger_level="L3",
            connector_type="CCS",
        )

        # Update expected strings to match your model's actual format
        self.assertEqual(
            ev_listing.get_charger_level_display(), "Level 3 (DC Fast Charging)"
        )
        self.assertEqual(
            ev_listing.get_connector_type_display(), "CCS (Combined Charging System)"
        )

    def test_filter_by_ev_charger(self):
        """Test filtering listings by EV charger attributes."""
        # Clear any existing listings to avoid test pollution
        Listing.objects.all().delete()

        # Create listings with different EV charger configurations
        Listing.objects.create(
            user=self.user,
            title="No Charger Spot",
            location="No Charger St",
            rent_per_hour=Decimal("20.00"),
            description="No charger here",
            has_ev_charger=False,
        )

        Listing.objects.create(
            user=self.user,
            title="L1 J1772 Spot",
            location="L1 St",
            rent_per_hour=Decimal("25.00"),
            description="Slow charging",
            has_ev_charger=True,
            charger_level="L1",
            connector_type="J1772",
        )

        Listing.objects.create(
            user=self.user,
            title="L2 Tesla Spot",
            location="L2 St",
            rent_per_hour=Decimal("30.00"),
            description="Medium charging",
            has_ev_charger=True,
            charger_level="L2",
            connector_type="TESLA",
        )

        # Test filter by has_ev_charger
        ev_listings = Listing.objects.filter(has_ev_charger=True)
        self.assertEqual(ev_listings.count(), 2)

        # Filter by charger_level AND has_ev_charger
        l2_listings = Listing.objects.filter(has_ev_charger=True, charger_level="L2")
        self.assertEqual(l2_listings.count(), 1)
        self.assertEqual(l2_listings[0].title, "L2 Tesla Spot")

        # Filter by connector_type AND has_ev_charger
        tesla_listings = Listing.objects.filter(
            has_ev_charger=True, connector_type="TESLA"
        )
        self.assertEqual(tesla_listings.count(), 1)
        self.assertEqual(tesla_listings[0].title, "L2 Tesla Spot")


class ListingSlotModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.listing = Listing.objects.create(
            user=self.user,
            title="Test Space",
            location="123 Test Street",
            rent_per_hour=Decimal("25.50"),
            description="Test description",
        )

        today = dt.date.today()
        self.slot = ListingSlot.objects.create(
            listing=self.listing,
            start_date=today,
            start_time=dt.time(9, 0),
            end_date=today,
            end_time=dt.time(17, 0),
        )

    def test_string_representation(self):
        """Test the string representation of a ListingSlot."""
        today = dt.date.today()
        expected_string = f"Test Space slot: {today} 09:00:00 - {today} 17:00:00"
        self.assertEqual(str(self.slot), expected_string)

    def test_listing_relationship(self):
        """Test the relationship between Listing and ListingSlot."""
        self.assertEqual(self.slot.listing, self.listing)
        self.assertIn(self.slot, self.listing.slots.all())
