# listings/views.py
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ListingForm, ListingSlotFormSet, validate_non_overlapping_slots
from .models import Listing

# Define half-hour choices for use in the search form
HALF_HOUR_CHOICES = [
    (f"{hour:02d}:{minute:02d}", f"{hour:02d}:{minute:02d}")
    for hour in range(24)
    for minute in (0, 30)
]

@login_required
def create_listing(request):
    if request.method == "POST":
        listing_form = ListingForm(request.POST)
        slot_formset = ListingSlotFormSet(request.POST)
        if listing_form.is_valid() and slot_formset.is_valid():
            try:
                validate_non_overlapping_slots(slot_formset)
            except:
                messages.error(request, "Overlapping slots detected. Please correct.")
                return render(
                    request,
                    "listings/create_listing.html",
                    {"form": listing_form, "slot_formset": slot_formset},
                )
            new_listing = listing_form.save(commit=False)
            new_listing.user = request.user
            new_listing.save()
            slot_formset.instance = new_listing
            slot_formset.save()
            messages.success(request, "Listing created successfully!")
            return redirect("view_listings")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        listing_form = ListingForm()
        slot_formset = ListingSlotFormSet()

    return render(
        request,
        "listings/create_listing.html",
        {"form": listing_form, "slot_formset": slot_formset},
    )



@login_required
def edit_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)
    if request.method == "POST":
        listing_form = ListingForm(request.POST, instance=listing)
        slot_formset = ListingSlotFormSet(request.POST, instance=listing)
        if listing_form.is_valid() and slot_formset.is_valid():
            listing_form.save()
            slot_formset.save()
            return redirect("manage_listings")
    else:
        listing_form = ListingForm(instance=listing)
        slot_formset = ListingSlotFormSet(instance=listing)

    return render(
        request,
        "listings/edit_listing.html",
        {"form": listing_form, "slot_formset": slot_formset, "listing": listing},
    )




def view_listings(request):
    all_listings = Listing.objects.all()

    # Extract common filter parameters
    max_price   = request.GET.get("max_price")
    filter_type = request.GET.get("filter_type", "single")  # "single" or "multiple"

    if max_price:
        try:
            max_price_val = float(max_price)
            all_listings = all_listings.filter(rent_per_hour__lte=max_price_val)
        except ValueError:
            pass

    if filter_type == "single":
        # Single continuous interval filter
        start_date = request.GET.get("start_date")  # e.g., "2025-03-12"
        end_date   = request.GET.get("end_date")
        start_time = request.GET.get("start_time")    # e.g., "10:00"
        end_time   = request.GET.get("end_time")      # e.g., "14:00"
        if start_date and end_date and start_time and end_time:
            try:
                user_start_str = f"{start_date} {start_time}"  # "2025-03-12 10:00"
                user_end_str   = f"{end_date} {end_time}"
                user_start_dt  = datetime.strptime(user_start_str, "%Y-%m-%d %H:%M")
                user_end_dt    = datetime.strptime(user_end_str, "%Y-%m-%d %H:%M")
                filtered = []
                for listing in all_listings:
                    if listing.is_available_for_range(user_start_dt, user_end_dt):
                        filtered.append(listing)
                all_listings = filtered
            except ValueError:
                pass

    elif filter_type == "multiple":
        # Multiple intervals filter.
        try:
            interval_count = int(request.GET.get("interval_count", "0"))
        except ValueError:
            interval_count = 0

        intervals = []
        for i in range(1, interval_count + 1):
            s_date = request.GET.get(f"start_date_{i}")
            e_date = request.GET.get(f"end_date_{i}")
            s_time = request.GET.get(f"start_time_{i}")
            e_time = request.GET.get(f"end_time_{i}")
            if s_date and e_date and s_time and e_time:
                try:
                    s_dt = datetime.strptime(f"{s_date} {s_time}", "%Y-%m-%d %H:%M")
                    e_dt = datetime.strptime(f"{e_date} {e_time}", "%Y-%m-%d %H:%M")
                    intervals.append((s_dt, e_dt))
                except ValueError:
                    continue

        if intervals:
            filtered = []
            for listing in all_listings:
                # The listing must be available for every requested interval.
                available_for_all = True
                for (s_dt, e_dt) in intervals:
                    if not listing.is_available_for_range(s_dt, e_dt):
                        available_for_all = False
                        break
                if available_for_all:
                    filtered.append(listing)
            all_listings = filtered

    # Add extra display information to each listing.
    for listing in all_listings:
        # Assuming your location is stored like "Address [lat, lng]"
        listing.location_name = listing.location.split("[")[0].strip()
        listing.avg_rating = listing.average_rating()

    context = {
        "listings": all_listings,
        "half_hour_choices": HALF_HOUR_CHOICES,
        "filter_type": filter_type,
        # Pass along single-interval filter fields
        "max_price": max_price or "",
        "start_date": request.GET.get("start_date", ""),
        "end_date": request.GET.get("end_date", ""),
        "start_time": request.GET.get("start_time", ""),
        "end_time": request.GET.get("end_time", ""),
        # For multiple intervals, also pass the interval_count and the individual interval fields as needed.
        "interval_count": request.GET.get("interval_count", "0"),
    }
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

    # Check for pending or approved bookings
    active_bookings = listing.booking_set.filter(status__in=["PENDING", "APPROVED"])

    if active_bookings.exists():
        # Instead of using messages, return directly to manage_listings with an error
        return render(
            request,
            "listings/manage_listings.html",
            {
                "listings": Listing.objects.filter(user=request.user),
                "delete_error": """Cannot delete listing with pending or approved bookings.
                Please handle those bookings first.""",
                "error_listing_id": listing_id,  # To highlight which listing has the error
            },
        )

    if request.method == "POST":
        listing.delete()
        return redirect("manage_listings")

    return render(request, "listings/confirm_delete.html", {"listing": listing})


def listing_reviews(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    reviews = listing.reviews.all()  # using the related_name set in the Review model
    return render(
        request,
        "listings/listing_reviews.html",
        {"listing": listing, "reviews": reviews},
    )
