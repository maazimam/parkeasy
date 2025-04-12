from django.test import TestCase
from reports.forms import ReportForm


class ReportFormTests(TestCase):

    def test_form_initialization(self):
        """Test that the form initializes with the correct fields."""
        form = ReportForm()
        self.assertEqual(len(form.fields), 2)
        self.assertIn("report_type", form.fields)
        self.assertIn("description", form.fields)

    def test_form_valid_data(self):
        """Test that the form validates with valid data."""
        form_data = {
            "report_type": "INAPPROPRIATE",
            "description": "This is a test description.",
        }
        form = ReportForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_missing_data(self):
        """Test that the form does not validate with missing data."""
        # Missing report_type
        form_data = {
            "description": "This is a test description.",
        }
        form = ReportForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("report_type", form.errors)

        # Missing description
        form_data = {
            "report_type": "INAPPROPRIATE",
        }
        form = ReportForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)

    def test_description_widget(self):
        """Test that the description field has the correct widget attributes."""
        form = ReportForm()
        self.assertEqual(form.fields["description"].widget.attrs["rows"], 4)
        self.assertEqual(
            form.fields["description"].widget.attrs["placeholder"],
            "Please provide details about why you are reporting this item...",
        )
