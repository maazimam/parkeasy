from django.test import TestCase
from django.contrib.auth.models import User
from listings.models import Listing, ListingSlot, Review
import datetime as dt
from decimal import Decimal
from unittest.mock import patch, MagicMock

class ListingModelTest(TestCase):
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create test listing
        self.listing = Listing.objects.create(
            user=self.user,
            title='Test Space',
            location='123 Test Street, Test City',
            rent_per_hour=Decimal('25.50'),
            description='A test space for testing purposes'
        )
    
    def test_listing_creation(self):
        """Test the creation of a listing with all required fields."""
        self.assertEqual(self.listing.title, 'Test Space')
        self.assertEqual(self.listing.location, '123 Test Street, Test City')
        self.assertEqual(self.listing.rent_per_hour, Decimal('25.50'))
        self.assertEqual(self.listing.description, 'A test space for testing purposes')
        self.assertEqual(self.listing.user, self.user)
        self.assertIsNotNone(self.listing.created_at)
        self.assertIsNotNone(self.listing.updated_at)
    
    def test_string_representation(self):
        """Test the string representation of a Listing."""
        expected_string = f"Test Space - 123 Test Street, Test City"
        self.assertEqual(str(self.listing), expected_string)
    
    def test_average_rating_no_reviews(self):
        """Test average_rating returns None when there are no reviews."""
        self.assertIsNone(self.listing.average_rating())
    
    
    def test_is_available_for_range_single_slot(self):
        """Test availability check with a single slot covering the entire range."""
        # Create a slot for today 9am-5pm
        today = dt.date.today()
        slot = ListingSlot.objects.create(
            listing=self.listing,
            start_date=today,
            start_time=dt.time(9, 0),
            end_date=today,
            end_time=dt.time(17, 0)
        )
        
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
            end_time=dt.time(17, 0)
        )
        
        ListingSlot.objects.create(
            listing=self.listing,
            start_date=tomorrow,
            start_time=dt.time(9, 0),
            end_date=tomorrow,
            end_time=dt.time(17, 0)
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
            end_time=dt.time(9, 0)
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
            end_time=dt.time(12, 0)
        )
        
        ListingSlot.objects.create(
            listing=self.listing,
            start_date=today,
            start_time=dt.time(14, 0),
            end_date=today,
            end_time=dt.time(17, 0)
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
            end_time=dt.time(17, 0)
        )
        
        # Exact match of the slot
        start_dt = dt.datetime.combine(today, dt.time(9, 0))
        end_dt = dt.datetime.combine(today, dt.time(17, 0))
        self.assertTrue(self.listing.is_available_for_range(start_dt, end_dt))

class ListingSlotModelTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.listing = Listing.objects.create(
            user=self.user,
            title='Test Space',
            location='123 Test Street',
            rent_per_hour=Decimal('25.50'),
            description='Test description'
        )
        
        today = dt.date.today()
        self.slot = ListingSlot.objects.create(
            listing=self.listing,
            start_date=today,
            start_time=dt.time(9, 0),
            end_date=today,
            end_time=dt.time(17, 0)
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