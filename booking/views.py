# booking/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import datetime as dt
from django.utils import timezone
from .models import Booking
from .forms import BookingForm, BookingSlotFormSet
from listings.models import Listing
from listings.forms import ReviewForm
from django.contrib import messages



@login_required
def book_listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    # Prevent owners from booking their own listing
    if request.user == listing.user:
        messages.error(request, "You cannot book your own parking spot.")
        return redirect("view_listings")

    if request.method == "POST":
        booking_form = BookingForm(request.POST)
        slot_formset = BookingSlotFormSet(request.POST)
        if booking_form.is_valid() and slot_formset.is_valid():
            # Create the Booking object
            booking = booking_form.save(commit=False)
            booking.user = request.user
            booking.listing = listing
            booking.status = "PENDING"
            booking.save()

            # Assign the booking to each slot form
            slot_formset.instance = booking
            slot_formset.save()

            # Calculate total price
            total_hours = 0
            for slot in booking.slots.all():
                start_dt = dt.datetime.combine(slot.start_date, slot.start_time)
                end_dt   = dt.datetime.combine(slot.end_date, slot.end_time)
                duration = (end_dt - start_dt).total_seconds() / 3600.0
                total_hours += duration

            # Multiply by listing's rent per hour
            booking.total_price = total_hours * float(listing.rent_per_hour)
            booking.save()

            messages.success(request, "Booking request created!")
            return redirect("my_bookings")  # or wherever you go
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        booking_form = BookingForm()
        slot_formset = BookingSlotFormSet()

    return render(
        request,
        "booking/book_listing.html",
        {
            "listing": listing,
            "booking_form": booking_form,
            "slot_formset": slot_formset,
        },
    )

@login_required
def cancel_booking(request, booking_id):
    """
    Allows a user to cancel (delete) a booking.
    """
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    booking.delete()
    return redirect("my_bookings")


@login_required
def manage_booking(request, booking_id, action):
    """
    Allows listing owners to approve or decline a booking request.
    """
    booking = get_object_or_404(Booking, pk=booking_id)

    # Ensure only the listing owner can approve/decline
    if request.user != booking.listing.user:
        return redirect("my_bookings")

    if action == "approve":
        booking.status = "APPROVED"
    elif action == "decline":
        booking.status = "DECLINED"
    booking.save()

    return redirect("manage_listings")


@login_required
def review_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)

    # Combine booking date and time into a naive datetime
    naive_booking_datetime = dt.datetime.combine(booking.booking_date, booking.start_time)
    # Make it offset-aware using the current timezone
    booking_datetime = timezone.make_aware(
        naive_booking_datetime, timezone.get_current_timezone()
    )

    if timezone.now() < booking_datetime:
        # Booking hasn't started yet
        return redirect("my_bookings")

    # Check if this booking has already been reviewed
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

    return render(request, "booking/review_booking.html", {"form": form, "booking": booking})


@login_required
def my_bookings(request):
    user_bookings = Booking.objects.filter(user=request.user).order_by("-created_at")
    now_naive = dt.datetime.now()
    
    # For each booking, create a list of slot info
    for booking in user_bookings:
        slots_info = []
        for slot in booking.slots.all():
            # Combine the date and start_time of each booking slot
            booking_datetime = dt.datetime.combine(slot.start_date, slot.start_time)
            has_started = now_naive >= booking_datetime
            slots_info.append({
                'booking_datetime': booking_datetime,
                'has_started': has_started,
                'slot': slot,
            })
        # Attach the list to the booking for use in the template
        booking.slots_info = slots_info

    return render(request, "booking/my_bookings.html", {"bookings": user_bookings})
