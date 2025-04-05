# bookings/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import datetime as dt
from django.utils import timezone
from django.http import JsonResponse
from .models import Booking, BookingSlot
from .forms import (
    BookingForm,
    BookingSlotFormSet,
    BookingSlotForm,
)  # Add BookingSlotForm here
from listings.models import Listing
from listings.forms import ReviewForm, HALF_HOUR_CHOICES
from django.db import transaction
from .utils import (
    block_out_booking,
    restore_booking_availability,
    generate_recurring_dates,
    generate_booking_slots,
)


@login_required
def available_times(request):
    listing_id = request.GET.get("listing_id")
    date_str = request.GET.get("date")
    ref_date_str = request.GET.get("ref_date")  # reference date from first interval
    max_time_str = request.GET.get("max_time")  # optional for start_time update
    min_time_str = request.GET.get("min_time")  # optional for end_time update
    if not listing_id or not date_str:
        return JsonResponse({"times": []})
    try:
        booking_date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"times": []})
    listing = get_object_or_404(Listing, pk=listing_id)

    # If a reference date is provided, get the listing slot covering it.
    ref_slot = None
    if ref_date_str:
        try:
            ref_date = dt.datetime.strptime(ref_date_str, "%Y-%m-%d").date()
        except ValueError:
            ref_date = None
        if ref_date:
            ref_slots = listing.slots.filter(
                start_date__lte=ref_date, end_date__gte=ref_date
            )
            if ref_slots.exists():
                ref_slot = ref_slots.first()

    # Get listing slots covering the requested booking_date.
    slots = listing.slots.filter(
        start_date__lte=booking_date, end_date__gte=booking_date
    )
    if ref_slot:
        slots = slots.filter(pk=ref_slot.pk)

    valid_times = set()
    for slot in slots:
        # Determine time range.
        if slot.start_time == slot.end_time:
            current_dt = dt.datetime.combine(booking_date, dt.time(0, 0))
            end_dt = current_dt + dt.timedelta(days=1)
        else:
            if booking_date == slot.start_date:
                current_dt = dt.datetime.combine(booking_date, slot.start_time)
            else:
                current_dt = dt.datetime.combine(booking_date, dt.time(0, 0))
            if booking_date == slot.end_date:
                end_dt = dt.datetime.combine(booking_date, slot.end_time)
            else:
                end_dt = dt.datetime.combine(
                    booking_date, dt.time(0, 0)
                ) + dt.timedelta(days=1)
        while current_dt <= end_dt:
            valid_times.add(current_dt.strftime("%H:%M"))
            current_dt += dt.timedelta(minutes=30)
    times = sorted(valid_times)
    if max_time_str:
        times = [t for t in times if t <= max_time_str]
    if min_time_str:
        times = [t for t in times if t >= min_time_str]
    print(
        "Returning times for listing",
        listing_id,
        "on",
        booking_date,
        "ref_date=",
        ref_date_str,
        ":",
        times,
    )
    return JsonResponse({"times": times})


@login_required
def book_listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    error_messages = []
    success_messages = []

    # Prevent owners from booking their own listing.
    if request.user == listing.user:
        error_messages.append("You cannot book your own parking spot.")
        return redirect("view_listings")

    if request.method == "POST":
        booking_form = BookingForm(request.POST)

        # Check if this is a recurring booking
        is_recurring = request.POST.get("is_recurring") == "true"

        if booking_form.is_valid():
            try:
                with transaction.atomic():
                    if not is_recurring:
                        # Handle regular booking (existing logic)
                        booking = booking_form.save(commit=False)
                        booking.user = request.user
                        booking.listing = listing
                        booking.status = "PENDING"
                        booking.save()  # Save now so that booking gets an ID.

                        # Use prefix="form" so that the inline formset matches POST keys.
                        slot_formset = BookingSlotFormSet(
                            request.POST,
                            instance=booking,
                            form_kwargs={"listing": listing},
                            prefix="form",
                        )

                        # Ensure each form knows its listing.
                        for form in slot_formset.forms:
                            form.listing = listing

                        if slot_formset.is_valid():
                            slot_formset.save()
                            total_hours = 0
                            for slot in booking.slots.all():
                                start_dt = dt.datetime.combine(
                                    slot.start_date, slot.start_time
                                )
                                end_dt = dt.datetime.combine(
                                    slot.end_date, slot.end_time
                                )
                                duration = (end_dt - start_dt).total_seconds() / 3600.0
                                total_hours += duration
                            booking.total_price = total_hours * float(
                                listing.rent_per_hour
                            )
                            booking.save()
                            success_messages.append("Booking request created!")
                            return redirect("my_bookings")
                        else:
                            raise ValueError(
                                "Please fix the errors in the booking form."
                            )
                    else:
                        # Handle recurring booking
                        # Get recurring booking parameters
                        start_date = request.POST.get("recurring-start_date")
                        start_time = request.POST.get("recurring-start_time")
                        end_time = request.POST.get("recurring-end_time")
                        pattern = request.POST.get("recurring_pattern", "daily")
                        is_overnight = request.POST.get("recurring-overnight") == "on"

                        # Pattern-specific validation and parsing
                        if pattern == "daily":
                            # For daily pattern, end_date is required
                            end_date = request.POST.get("recurring-end_date")
                            if not all([start_date, start_time, end_time, end_date]):
                                raise ValueError(
                                    """Start date, end date, start time, and end time
                                    are required for daily recurring bookings."""
                                )

                            # Convert strings to date/time objects
                            start_date = dt.datetime.strptime(
                                start_date, "%Y-%m-%d"
                            ).date()
                            start_time = dt.datetime.strptime(
                                start_time, "%H:%M"
                            ).time()
                            end_time = dt.datetime.strptime(end_time, "%H:%M").time()
                            end_date = dt.datetime.strptime(end_date, "%Y-%m-%d").date()

                            # Validate end date
                            if end_date < start_date:
                                raise ValueError(
                                    "End date must be on or after start date."
                                )

                            # Generate dates for daily pattern
                            dates = generate_recurring_dates(
                                start_date, "daily", end_date=end_date
                            )

                        elif pattern == "weekly":
                            # For weekly pattern, only start_date, start_time, end_time required
                            if not all([start_date, start_time, end_time]):
                                raise ValueError(
                                    """Start date, start time, and end time are
                                    required for weekly recurring bookings."""
                                )

                            # Convert strings to date/time objects
                            start_date = dt.datetime.strptime(
                                start_date, "%Y-%m-%d"
                            ).date()
                            start_time = dt.datetime.strptime(
                                start_time, "%H:%M"
                            ).time()
                            end_time = dt.datetime.strptime(end_time, "%H:%M").time()

                            # Get number of weeks
                            weeks_str = request.POST.get("recurring-weeks")
                            if not weeks_str:
                                raise ValueError(
                                    "Number of weeks is required for weekly recurring pattern."
                                )

                            weeks = int(weeks_str)
                            if weeks <= 0 or weeks > 52:
                                raise ValueError(
                                    "Number of weeks must be between 1 and 52."
                                )

                            # Generate dates for weekly pattern
                            dates = generate_recurring_dates(
                                start_date, "weekly", weeks=weeks
                            )

                        # Validate start/end time logic for non-overnight bookings
                        if start_time >= end_time and not is_overnight:
                            raise ValueError(
                                "Start time must be before end time unless overnight booking is selected."
                            )

                        # Generate booking slots from dates
                        booking_slots = generate_booking_slots(
                            dates, start_time, end_time, is_overnight
                        )

                        # Check if all slots are available
                        unavailable_dates = []
                        for slot in booking_slots:
                            start_dt = dt.datetime.combine(
                                slot["start_date"], slot["start_time"]
                            )
                            end_dt = dt.datetime.combine(
                                slot["end_date"], slot["end_time"]
                            )
                            start_dt = timezone.make_aware(start_dt)
                            end_dt = timezone.make_aware(end_dt)

                            # Check if this time range is within any available listing slot
                            if not listing.is_available_for_range(start_dt, end_dt):
                                date_str = slot["start_date"].strftime("%Y-%m-%d")
                                unavailable_dates.append(date_str)

                        # If any date is unavailable, return error
                        if unavailable_dates:
                            error_msg = """Sorry, some of those times are not available.
                                        Please review the available times and try again."""
                            # Don't add to error_messages here, just raise the error
                            raise ValueError(error_msg)

                        # All slots are available, create the booking
                        booking = booking_form.save(commit=False)
                        booking.user = request.user
                        booking.listing = listing
                        booking.status = "PENDING"
                        booking.save()

                        # Create all booking slots
                        total_hours = 0
                        for slot_data in booking_slots:
                            slot = BookingSlot(
                                booking=booking,
                                start_date=slot_data["start_date"],
                                start_time=slot_data["start_time"],
                                end_date=slot_data["end_date"],
                                end_time=slot_data["end_time"],
                            )
                            slot.save()

                            # Calculate hours for pricing
                            start_dt = dt.datetime.combine(
                                slot_data["start_date"], slot_data["start_time"]
                            )
                            end_dt = dt.datetime.combine(
                                slot_data["end_date"], slot_data["end_time"]
                            )
                            duration = (end_dt - start_dt).total_seconds() / 3600.0
                            total_hours += duration

                        # Update total price
                        booking.total_price = total_hours * float(listing.rent_per_hour)
                        booking.save()

                        success_messages.append(
                            f"Recurring booking created successfully for {len(booking_slots)} dates!"
                        )
                        return redirect("my_bookings")

            except ValueError as e:
                # Handle ValueError by adding to error_messages
                error_messages.append(str(e))

                # Re-instantiate the formset for rendering
                slot_formset = BookingSlotFormSet(
                    form_kwargs={"listing": listing}, prefix="form"
                )

            except Exception as e:
                # Catch any other exceptions
                error_messages.append(f"An error occurred: {str(e)}")

                # Re-instantiate the formset for rendering
                slot_formset = BookingSlotFormSet(
                    form_kwargs={"listing": listing}, prefix="form"
                )
        else:
            # Instantiate the formset so it can be rendered with errors.
            slot_formset = BookingSlotFormSet(
                request.POST,
                form_kwargs={"listing": listing},
                prefix="form",
            )
            error_messages.append("Please fix the errors below.")
    else:
        booking_form = BookingForm()
        slot_formset = BookingSlotFormSet(
            form_kwargs={"listing": listing}, prefix="form"
        )

    # Create a dedicated form instance for the recurring interface
    recurring_form = BookingSlotForm(prefix="recurring", listing=listing)

    return render(
        request,
        "booking/book_listing.html",
        {
            "listing": listing,
            "booking_form": booking_form,
            "slot_formset": slot_formset,
            "recurring_form": recurring_form,  # Add this
            "half_hour_choices": HALF_HOUR_CHOICES,
            "error_messages": error_messages,
            "success_messages": success_messages,
        },
    )


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    if booking.status == "APPROVED":
        restore_booking_availability(booking.listing, booking)
    booking.delete()
    return redirect("my_bookings")


@login_required
def manage_booking(request, booking_id, action):
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.user != booking.listing.user:
        return redirect("my_bookings")
    if action == "approve":
        booking.status = "APPROVED"
        booking.save()
        block_out_booking(booking.listing, booking)
        # (Call block_out_booking(booking.listing, booking) here if you want to block times.)
    elif action == "decline":
        if booking.status == "APPROVED":
            restore_booking_availability(booking.listing, booking)
        booking.status = "DECLINED"
        booking.save()
        # (Call restore_booking_availability(booking.listing, booking) here if needed.)
    return redirect("manage_listings")


@login_required
def review_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    # Determine earliest slot start to decide if booking has started.
    earliest_slot = min(
        (
            dt.datetime.combine(slot.start_date, slot.start_time)
            for slot in booking.slots.all()
        ),
        default=None,
    )
    if earliest_slot:
        booking_datetime = timezone.make_aware(
            earliest_slot, timezone.get_current_timezone()
        )
        if timezone.now() < booking_datetime:
            return redirect("my_bookings")
    else:
        return redirect("my_bookings")

    if hasattr(booking, "review"):
        return redirect("my_bookings")

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.listing = booking.listing
            review.user = request.user
            review.save()
            return redirect("my_bookings")
    else:
        form = ReviewForm()
    return render(
        request, "booking/review_booking.html", {"form": form, "booking": booking}
    )


@login_required
def my_bookings(request):
    user_bookings = Booking.objects.filter(user=request.user).order_by("-created_at")
    now_naive = dt.datetime.now()
    for booking in user_bookings:
        slots_info = []
        for slot in booking.slots.all():
            slot_dt = dt.datetime.combine(slot.start_date, slot.start_time)
            has_started = now_naive >= slot_dt
            slots_info.append(
                {
                    "booking_datetime": slot_dt,
                    "has_started": has_started,
                    "slot": slot,
                }
            )
        booking.slots_info = slots_info
    return render(request, "booking/my_bookings.html", {"bookings": user_bookings})
