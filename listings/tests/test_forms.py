from decimal import Decimal
from django.test import TestCase
from django import forms
from django.contrib.auth import get_user_model
from listings.forms import ListingForm, validate_non_overlapping_slots
import datetime


class MockForm:
    def __init__(self, cleaned_data):
        self.cleaned_data = cleaned_data


class TestValidateNonOverlappingSlots(TestCase):
    def test_non_overlapping_slots_pass_validation(self):
        """Test that non-overlapping slots pass validation."""
        formset = [
            MockForm(
                {
                    "start_date": datetime.date(2023, 1, 1),
                    "start_time": "09:00",
                    "end_date": datetime.date(2023, 1, 1),
                    "end_time": "12:00",
                }
            ),
            MockForm(
                {
                    "start_date": datetime.date(2023, 1, 1),
                    "start_time": "13:00",
                    "end_date": datetime.date(2023, 1, 1),
                    "end_time": "15:00",
                }
            ),
            MockForm(
                {
                    "start_date": datetime.date(2023, 1, 2),
                    "start_time": "09:00",
                    "end_date": datetime.date(2023, 1, 2),
                    "end_time": "12:00",
                }
            ),
        ]

        # Should not raise an exception
        validate_non_overlapping_slots(formset)

    def test_adjacent_slots_pass_validation(self):
        """Test that adjacent slots (one ends when another begins) pass validation."""
        formset = [
            MockForm(
                {
                    "start_date": datetime.date(2023, 1, 1),
                    "start_time": "09:00",
                    "end_date": datetime.date(2023, 1, 1),
                    "end_time": "12:00",
                }
            ),
            MockForm(
                {
                    "start_date": datetime.date(2023, 1, 1),
                    "start_time": "12:00",
                    "end_date": datetime.date(2023, 1, 1),
                    "end_time": "15:00",
                }
            ),
        ]

        # Should not raise an exception
        validate_non_overlapping_slots(formset)

    def test_overlapping_slots_fail_validation(self):
        """Test that overlapping slots fail validation."""
        formset = [
            MockForm(
                {
                    "start_date": datetime.date(2023, 1, 1),
                    "start_time": "09:00",
                    "end_date": datetime.date(2023, 1, 1),
                    "end_time": "12:00",
                }
            ),
            MockForm(
                {
                    "start_date": datetime.date(2023, 1, 1),
                    "start_time": "11:00",
                    "end_date": datetime.date(2023, 1, 1),
                    "end_time": "14:00",
                }
            ),
        ]

        # Should raise ValidationError
        with self.assertRaises(forms.ValidationError):
            validate_non_overlapping_slots(formset)

    def test_overlapping_across_days_fail_validation(self):
        """Test that slots overlapping across days fail validation."""
        formset = [
            MockForm(
                {
                    "start_date": datetime.date(2023, 1, 1),
                    "start_time": "20:00",
                    "end_date": datetime.date(2023, 1, 2),
                    "end_time": "10:00",
                }
            ),
            MockForm(
                {
                    "start_date": datetime.date(2023, 1, 2),
                    "start_time": "09:00",
                    "end_date": datetime.date(2023, 1, 2),
                    "end_time": "12:00",
                }
            ),
        ]

        # Should raise ValidationError
        with self.assertRaises(forms.ValidationError):
            validate_non_overlapping_slots(formset)

    def test_deleted_form_ignored(self):
        """Test that forms marked for deletion are ignored in validation."""
        formset = [
            MockForm(
                {
                    "start_date": datetime.date(2023, 1, 1),
                    "start_time": "09:00",
                    "end_date": datetime.date(2023, 1, 1),
                    "end_time": "12:00",
                }
            ),
            MockForm(
                {
                    "start_date": datetime.date(2023, 1, 1),
                    "start_time": "11:00",
                    "end_date": datetime.date(2023, 1, 1),
                    "end_time": "14:00",
                    "DELETE": True,  # This form should be ignored
                }
            ),
        ]

        # Should not raise an exception because the overlapping form is marked for deletion
        validate_non_overlapping_slots(formset)

    def test_incomplete_form_data_handled(self):
        """Test that forms with missing fields don't cause errors."""
        formset = [
            MockForm(
                {
                    "start_date": datetime.date(2023, 1, 1),
                    "start_time": "09:00",
                    "end_date": datetime.date(2023, 1, 1),
                    "end_time": "12:00",
                }
            ),
            MockForm(
                {
                    "start_date": datetime.date(2023, 1, 1),
                    # Missing start_time
                    "end_date": datetime.date(2023, 1, 1),
                    "end_time": "14:00",
                }
            ),
        ]

        # Should not raise an exception as incomplete forms are skipped
        validate_non_overlapping_slots(formset)


class TestEVChargerForm(TestCase):
    def setUp(self):
        self.form_data = {
            "title": "Test Parking Space",
            "location": "POINT(1 1)",
            "rent_per_hour": Decimal("25.00"),
            "description": "A nice parking space for testing",
        }

    def test_ev_charger_required_fields(self):
        """Test that charger_level and connector_type are required when has_ev_charger=True"""
        # Form with has_ev_charger=True but missing charger fields
        data = self.form_data.copy()
        data["has_ev_charger"] = True

        form = ListingForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("charger_level", form.errors)
        self.assertIn("connector_type", form.errors)

        # Adding the required fields should make the form valid
        data["charger_level"] = "L2"
        data["connector_type"] = "J1772"

        form = ListingForm(data=data)
        self.assertTrue(form.is_valid())

    def test_ev_fields_cleared_when_no_charger(self):
        """Test that charger fields are cleared when has_ev_charger=False"""
        data = self.form_data.copy()
        data["has_ev_charger"] = False
        data["charger_level"] = "L3"  # Should be cleared
        data["connector_type"] = "TESLA"  # Should be cleared

        form = ListingForm(data=data)
        self.assertTrue(form.is_valid())

        # Test that the cleaned data has empty charger fields
        listing = form.save(commit=False)
        self.assertEqual(listing.charger_level, "")
        self.assertEqual(listing.connector_type, "")

    def test_form_field_attributes(self):
        """Test that EV charger form fields have the correct attributes"""
        form = ListingForm()

        # Check CSS classes
        self.assertIn(
            "ev-charger-option",
            form.fields["charger_level"].widget.attrs.get("class", ""),
        )
        self.assertIn(
            "ev-charger-option",
            form.fields["connector_type"].widget.attrs.get("class", ""),
        )

    def test_initial_disabled_state(self):
        """Test that charger fields are initially disabled based on has_ev_charger"""
        # When has_ev_charger is initially False
        form = ListingForm(initial={"has_ev_charger": False})

        self.assertIn("disabled", form.fields["charger_level"].widget.attrs)
        self.assertIn("disabled", form.fields["connector_type"].widget.attrs)

        # When has_ev_charger is initially True
        form = ListingForm(initial={"has_ev_charger": True})

        self.assertNotIn("disabled", form.fields["charger_level"].widget.attrs)
        self.assertNotIn("disabled", form.fields["connector_type"].widget.attrs)

    def test_editing_listing_with_ev_charger(self):
        """Test editing a listing that already has EV charger info"""
        user = get_user_model().objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

        from listings.models import Listing

        # Create a listing with EV charger
        existing_listing = Listing.objects.create(
            user=user,
            title="Existing EV Spot",
            location="POINT(1 1)",
            rent_per_hour=Decimal("30.00"),
            description="Already has EV charger",
            has_ev_charger=True,
            charger_level="L2",
            connector_type="J1772",
        )

        # Test form loads with correct initial values
        form = ListingForm(instance=existing_listing)
        self.assertTrue(form.initial["has_ev_charger"])
        self.assertEqual(form.initial["charger_level"], "L2")
        self.assertEqual(form.initial["connector_type"], "J1772")

        # Test updating EV info
        data = {
            "title": "Updated EV Spot",
            "location": "POINT(1 1)",
            "rent_per_hour": Decimal("35.00"),
            "description": "Updated description",
            "has_ev_charger": True,
            "charger_level": "L3",
            "connector_type": "TESLA",
        }

        update_form = ListingForm(data=data, instance=existing_listing)
        self.assertTrue(update_form.is_valid())

        updated_listing = update_form.save()
        self.assertEqual(updated_listing.charger_level, "L3")
        self.assertEqual(updated_listing.connector_type, "TESLA")

    def test_changing_ev_charger_status(self):
        """Test changing a listing from having EV charger to not having one"""
        user = get_user_model().objects.create_user(
            username="testuser2", email="test2@example.com", password="password123"
        )

        from listings.models import Listing

        # Create a listing with EV charger
        existing_listing = Listing.objects.create(
            user=user,
            title="EV Spot to Update",
            location="POINT(1 1)",
            rent_per_hour=Decimal("30.00"),
            description="Has EV charger initially",
            has_ev_charger=True,
            charger_level="L2",
            connector_type="J1772",
        )

        # Change to no EV charger
        data = {
            "title": "No Longer EV Spot",
            "location": "POINT(1 1)",
            "rent_per_hour": Decimal("25.00"),
            "description": "No longer has EV charger",
            "has_ev_charger": False,
            # Including values that should be cleared
            "charger_level": "L2",
            "connector_type": "J1772",
        }

        update_form = ListingForm(data=data, instance=existing_listing)
        self.assertTrue(update_form.is_valid())

        updated_listing = update_form.save()
        self.assertFalse(updated_listing.has_ev_charger)
        self.assertEqual(updated_listing.charger_level, "")
        self.assertEqual(updated_listing.connector_type, "")
