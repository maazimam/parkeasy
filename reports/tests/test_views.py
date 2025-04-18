from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from messaging.models import Message
from listings.models import Listing
from reports.models import Report


class ReportTests(TestCase):
    def setUp(self):
        # Create test users
        self.owner = User.objects.create_user(
            username="parkowner", email="owner@example.com", password="testpass123"
        )
        self.parker = User.objects.create_user(
            username="parker", email="parker@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )

        # Create a test listing
        self.listing = Listing.objects.create(
            user=self.owner,
            title="Test Parking Spot",
            location="123 Test St",
            rent_per_hour=10.00,
            description="A test parking spot",
        )

        # Create test messages
        self.message_from_parker = Message.objects.create(
            sender=self.parker,
            recipient=self.owner,
            subject="Inquiry about spot",
            body="I'd like to book your spot",
        )

        self.message_from_owner = Message.objects.create(
            sender=self.owner,
            recipient=self.parker,
            subject="Re: Inquiry",
            body="Sure, it's available",
        )

        # Get content types
        self.message_content_type = ContentType.objects.get_for_model(Message)
        self.listing_content_type = ContentType.objects.get_for_model(Listing)

        # Set up client
        self.client = Client()

    def test_report_message_by_recipient(self):
        """Test that a message recipient can report a message"""
        self.client.login(username="parker", password="testpass123")

        response = self.client.post(
            reverse("report_item", args=["message", self.message_from_owner.id]),
            {
                "report_type": "INAPPROPRIATE",
                "description": "This message is inappropriate",
            },
        )

        # Check redirect
        self.assertRedirects(response, reverse("inbox"))

        # Check report was created
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.first()
        self.assertEqual(report.reporter, self.parker)
        self.assertEqual(report.content_type, self.message_content_type)
        self.assertEqual(report.object_id, self.message_from_owner.id)
        self.assertEqual(report.report_type, "INAPPROPRIATE")

    def test_report_message_by_sender(self):
        """Test that a message sender can report a message"""
        self.client.login(username="parkowner", password="testpass123")

        response = self.client.post(
            reverse("report_item", args=["message", self.message_from_owner.id]),
            {"report_type": "SPAM", "description": "I want to report my own message"},
        )

        # Check redirect
        self.assertRedirects(response, reverse("inbox"))

        # Check report was created
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.first()
        self.assertEqual(report.reporter, self.owner)
        self.assertEqual(report.content_type, self.message_content_type)
        self.assertEqual(report.object_id, self.message_from_owner.id)
        self.assertEqual(report.report_type, "SPAM")

    def test_cannot_report_others_message(self):
        """Test that users cannot report messages they're not part of"""
        self.client.login(username="otheruser", password="testpass123")

        response = self.client.get(
            reverse("report_item", args=["message", self.message_from_owner.id])
        )

        # Should redirect away without creating report
        self.assertRedirects(response, reverse("inbox"))
        self.assertEqual(Report.objects.count(), 0)

    def test_report_listing(self):
        """Test reporting a listing"""
        self.client.login(username="parker", password="testpass123")

        response = self.client.post(
            reverse("report_item", args=["listing", self.listing.id]),
            {
                "report_type": "MISLEADING",
                "description": "The listing information is incorrect",
            },
        )

        # Check redirect
        self.assertRedirects(response, reverse("view_listings"))

        # Check report was created
        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.first()
        self.assertEqual(report.reporter, self.parker)
        self.assertEqual(report.content_type, self.listing_content_type)
        self.assertEqual(report.object_id, self.listing.id)
        self.assertEqual(report.report_type, "MISLEADING")

    def test_report_nonexistent_object(self):
        """Test handling of reports for objects that don't exist"""
        self.client.login(username="parker", password="testpass123")

        response = self.client.get(
            reverse("report_item", args=["listing", 99999])  # Non-existent ID
        )

        # Don't fetch the redirect response
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertEqual(Report.objects.count(), 0)

    def test_report_invalid_content_type(self):
        """Test handling of invalid content types"""
        self.client.login(username="parker", password="testpass123")

        response = self.client.get(reverse("report_item", args=["invalid_type", 1]))

        # Don't fetch the redirect response
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertEqual(Report.objects.count(), 0)

    def test_login_required(self):
        """Test that login is required to report"""
        # Not logged in
        response = self.client.get(
            reverse("report_item", args=["listing", self.listing.id])
        )

        # Should redirect to login
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('report_item', args=['listing', self.listing.id])}",
        )
