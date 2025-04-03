from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (ListingForm, ListingSlotForm, ListingSlotFormSet,
                    validate_non_overlapping_slots)
from .models import Listing, ListingSlot
from .utils import calculate_distance, extract_coordinates, simplify_location

# Define an inline formset for editing (extra=0)
ListingSlotFormSetEdit = inlineformset_factory(
    Listing, ListingSlot, form=ListingSlotForm, extra=0, can_delete=True
)

# Define half-hour choices for use in the search form
HALF_HOUR_CHOICES = [
    (f"{hour:02d}:{minute:02d}", f"{hour:02d}:{minute:02d}")
    for hour in range(24)
    for minute in (0, 30)
]


@login_required
def create_listing(request):
    alert_message = ""
    if request.method == "POST":
        listing_form = ListingForm(request.POST)
        slot_formset = ListingSlotFormSet(request.POST, prefix="form")
        if listing_form.is_valid() and slot_formset.is_valid():
            try:
                validate_non_overlapping_slots(slot_formset)
            except Exception:
                alert_message = "Overlapping slots detected. Please correct."
                return render(
                    request,
                    "listings/create_listing.html",
                    {
                        "form": listing_form,
                        "slot_formset": slot_formset,
                        "alert_message": alert_message,
                    },
                )
            new_listing = listing_form.save(commit=False)
            new_listing.user = request.user
            new_listing.save()
            slot_formset.instance = new_listing
            slot_formset.save()
            messages.success(request, "Listing created successfully!")
            return redirect("view_listings")
        else:
            alert_message = "Please correct the errors below."
    else:
        listing_form = ListingForm()
        slot_formset = ListingSlotFormSet(prefix="form")
    return render(
        request,
        "listings/create_listing.html",
        {
            "form": listing_form,
            "slot_formset": slot_formset,
            "alert_message": alert_message,
        },
    )


@login_required
def edit_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)
    alert_message = ""
    current_dt = datetime.now()

    if request.method == "POST":
        listing_form = ListingForm(request.POST, instance=listing)
        slot_formset = ListingSlotFormSetEdit(
            request.POST, instance=listing, prefix="form"
        )
        if listing_form.is_valid() and slot_formset.is_valid():
            try:
                validate_non_overlapping_slots(slot_formset)
            except Exception:
                alert_message = "Overlapping slots detected. Please correct."
                return render(
                    request,
                    "listings/edit_listing.html",
                    {
                        "form": listing_form,
                        "slot_formset": slot_formset,
                        "listing": listing,
                        "alert_message": alert_message,
                    },
                )

            # Block editing if there is any pending booking.
            pending_bookings = listing.booking_set.filter(status="PENDING")
            if pending_bookings.exists():
                alert_message = (
                    "You cannot edit your listing while there is a pending booking. "
                    "Please accept or reject all pending bookings before editing."
                )
                return render(
                    request,
                    "listings/edit_listing.html",
                    {
                        "form": listing_form,
                        "slot_formset": slot_formset,
                        "listing": listing,
                        "alert_message": alert_message,
                    },
                )

            # Build new intervals from the formset.
            new_intervals = []
            for form in slot_formset:
                if form.cleaned_data.get("DELETE"):
                    continue
                start_date = form.cleaned_data.get("start_date")
                start_time = form.cleaned_data.get("start_time")
                end_date = form.cleaned_data.get("end_date")
                end_time = form.cleaned_data.get("end_time")
                if start_date and start_time and end_date and end_time:
                    st = (
                        start_time
                        if isinstance(start_time, time)
                        else datetime.strptime(start_time, "%H:%M").time()
                    )
                    et = (
                        end_time
                        if isinstance(end_time, time)
                        else datetime.strptime(end_time, "%H:%M").time()
                    )
                    start_dt = datetime.combine(start_date, st)
                    end_dt = datetime.combine(end_date, et)
                    new_intervals.append((start_dt, end_dt))

            # Merge intervals into non-overlapping ranges.
            new_intervals.sort(key=lambda iv: iv[0])
            merged_intervals = []
            for interval in new_intervals:
                if not merged_intervals:
                    merged_intervals.append(interval)
                else:
                    last_start, last_end = merged_intervals[-1]
                    if interval[0] <= last_end:
                        merged_intervals[-1] = (last_start, max(last_end, interval[1]))
                    else:
                        merged_intervals.append(interval)

            # BLOCK EDIT IF ANY NEW INTERVAL OVERLAPS WITH ANY APPROVED BOOKING SLOT
            active_bookings = listing.booking_set.filter(status="APPROVED")
            for booking in active_bookings:
                for slot in booking.slots.all():
                    booking_start = datetime.combine(slot.start_date, slot.start_time)
                    booking_end = datetime.combine(slot.end_date, slot.end_time)
                    for interval_start, interval_end in merged_intervals:
                        if (
                            interval_start < booking_end
                            and booking_start < interval_end
                        ):
                            alert_message = (
                                "Your changes conflict with an active booking. "
                                "You cannot edit when new availability overlaps with an approved booking."
                            )
                            return render(
                                request,
                                "listings/edit_listing.html",
                                {
                                    "form": listing_form,
                                    "slot_formset": slot_formset,
                                    "listing": listing,
                                    "alert_message": alert_message,
                                },
                            )

            # Save the changes.
            listing_form.save()
            slot_formset.save()

            # Delete any timeslots that have already passed.
            for slot in listing.slots.all():
                slot_end = datetime.combine(slot.end_date, slot.end_time)
                if slot_end <= datetime.now():
                    slot.delete()

            messages.success(request, "Listing updated successfully!")
            return redirect("manage_listings")
        else:
            alert_message = "Please correct the errors below."
    else:
        # GET: Pre-process timeslots.
        all_slots = listing.slots.all()
        non_passed_ids = [
            slot.id
            for slot in all_slots
            if datetime.combine(slot.end_date, slot.end_time) > current_dt
        ]
        non_passed_qs = listing.slots.filter(id__in=non_passed_ids)
        listing_form = ListingForm(instance=listing)
        slot_formset = ListingSlotFormSetEdit(
            instance=listing, prefix="form", queryset=non_passed_qs
        )
        # For any ongoing slot, update its initial start_time to the next half‑hour slot.
        for form in slot_formset.forms:
            slot = form.instance
            slot_start_dt = datetime.combine(slot.start_date, slot.start_time)
            slot_end_dt = datetime.combine(slot.end_date, slot.end_time)
            if slot_start_dt <= current_dt < slot_end_dt:
                minutes = current_dt.minute
                if minutes < 30:
                    new_minute = 30
                    new_hour = current_dt.hour
                else:
                    new_minute = 0
                    new_hour = current_dt.hour + 1
                    if new_hour >= 24:
                        new_hour -= 24
                form.initial["start_time"] = f"{new_hour:02d}:{new_minute:02d}"

    return render(
        request,
        "listings/edit_listing.html",
        {
            "form": listing_form,
            "slot_formset": slot_formset,
            "listing": listing,
            "alert_message": alert_message,
        },
    )


def view_listings(request):
    # Get filter parameters
    filter_type = request.GET.get("filter_type", "single")
    max_price = request.GET.get("max_price")
    search_lat = request.GET.get('lat')
    search_lng = request.GET.get('lng')
    radius = request.GET.get('radius')
    error_messages = []
    warning_messages = []

    # Base queryset
    listings = Listing.objects.all().prefetch_related('reviews')

    # Apply price filter if specified
    if max_price:
        try:
            max_price = float(max_price)
            listings = listings.filter(rent_per_hour__lte=max_price)
        except ValueError:
            error_messages.append("Invalid price filter")

    # Filter by location proximity if coordinates provided
    processed_listings = []
    if search_lat and search_lng:
        try:
            search_lat = float(search_lat)
            search_lng = float(search_lng)

            for listing in listings:
                try:
                    # Extract listing coordinates
                    listing_lat, listing_lng = extract_coordinates(listing.location)

                    # Calculate distance
                    distance = calculate_distance(
                        search_lat, search_lng,
                        listing_lat, listing_lng
                    )

                    # Add distance to listing object
                    listing.distance = distance

                    # Only apply radius filter if specified
                    if radius:
                        radius = float(radius)
                        if distance <= radius:
                            processed_listings.append(listing)
                    else:
                        processed_listings.append(listing)
                except ValueError:
                    listing.distance = None  # Set distance to None if coordinates invalid
                    processed_listings.append(listing)  # Still include the listing
        except ValueError:
            error_messages.append("Invalid coordinates provided")
            processed_listings = list(listings)  # Use all listings if coordinates invalid
    else:
        # If no location search, process listings normally
        for listing in listings:
            listing.distance = None  # Set distance to None when no search location
            processed_listings.append(listing)

    # Sort by distance if we have coordinates
    if search_lat and search_lng:
        processed_listings.sort(key=lambda x: x.distance if x.distance is not None else float('inf'))

    # Process availability info for all listings
    for listing in processed_listings:
        try:
            earliest_slot = listing.slots.earliest('start_date', 'start_time')
            listing.available_from = earliest_slot.start_date
            listing.available_time_from = earliest_slot.start_time
            latest_slot = listing.slots.latest('end_date', 'end_time')
            listing.available_until = latest_slot.end_date
            listing.available_time_until = latest_slot.end_time
        except listing.slots.model.DoesNotExist:
            listing.available_from = None
            listing.available_time_from = None
            listing.available_until = None
            listing.available_time_until = None

    # Pagination logic
    page_number = request.GET.get("page", 1)
    paginator = Paginator(processed_listings, 10)
    page_obj = paginator.get_page(page_number)

    context = {
        "listings": page_obj,
        "half_hour_choices": HALF_HOUR_CHOICES,
        "filter_type": filter_type,
        "max_price": max_price or "",
        "search_lat": search_lat,
        "search_lng": search_lng,
        "radius": radius,
        "start_date": request.GET.get("start_date", ""),
        "end_date": request.GET.get("end_date", ""),
        "start_time": request.GET.get("start_time", ""),
        "end_time": request.GET.get("end_time", ""),
        "recurring_pattern": request.GET.get("recurring_pattern", "daily"),
        "recurring_start_date": request.GET.get("recurring_start_date", ""),
        "recurring_end_date": request.GET.get("recurring_end_date", ""),
        "recurring_start_time": request.GET.get("recurring_start_time", ""),
        "recurring_end_time": request.GET.get("recurring_end_time", ""),
        "recurring_weeks": request.GET.get("recurring_weeks", "4"),
        "recurring_overnight": "on" if request.GET.get("recurring_overnight") else "",
        "has_next": page_obj.has_next(),
        "next_page": int(page_number) + 1 if page_obj.has_next() else None,
        "error_messages": error_messages,
        "warning_messages": warning_messages,
    }

    if request.GET.get("ajax") == "1":
        return render(request, "listings/partials/listing_cards.html", context)
    return render(request, "listings/view_listings.html", context)


def manage_listings(request):
    owner_listings = Listing.objects.filter(user=request.user)
    for listing in owner_listings:
        listing.pending_bookings = listing.booking_set.filter(status="PENDING")
        listing.approved_bookings = listing.booking_set.filter(status="APPROVED")
    return render(
        request, "listings/manage_listings.html", {"listings": owner_listings}
    )


@login_required
def delete_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)
    active_bookings = listing.booking_set.filter(status__in=["PENDING", "APPROVED"])
    if active_bookings.exists():
        owner_listings = Listing.objects.filter(user=request.user)
        for lst in owner_listings:
            lst.pending_bookings = lst.booking_set.filter(status="PENDING")
            lst.approved_bookings = lst.booking_set.filter(status="APPROVED")
        return render(
            request,
            "listings/manage_listings.html",
            {
                "listings": owner_listings,
                "delete_error": "Cannot delete listing with pending bookings. Please handle those first.",
                "error_listing_id": listing_id,
            },
        )
    if request.method == "POST":
        listing.delete()
        return redirect("manage_listings")
    return render(request, "listings/confirm_delete.html", {"listing": listing})


def listing_reviews(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    reviews = listing.reviews.all()
    return render(
        request,
        "listings/listing_reviews.html",
        {"listing": listing, "reviews": reviews},
    )