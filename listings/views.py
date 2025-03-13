# listings/views.py
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ListingForm, ListingSlotFormSet
from .models import Listing



@login_required
def create_listing(request):
    if request.method == "POST":
        listing_form = ListingForm(request.POST)
        slot_formset = ListingSlotFormSet(request.POST)
        if listing_form.is_valid() and slot_formset.is_valid():
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

    # Extract GET parameters
    max_price = request.GET.get("max_price")
    start_date = request.GET.get("start_date")  # e.g. "2025-03-12"
    end_date = request.GET.get("end_date")
    start_time = request.GET.get("start_time")  # e.g. "10:00"
    end_time = request.GET.get("end_time")

    # Filter by max price if given
    if max_price:
        try:
            max_price_val = float(max_price)
            all_listings = all_listings.filter(rent_per_hour__lte=max_price_val)
        except ValueError:
            pass

    # If we have a full set of date/time params, do the advanced filter
    if start_date and end_date and start_time and end_time:
        try:
            user_start_str = f"{start_date} {start_time}"  # "2025-03-12 10:00"
            user_end_str   = f"{end_date} {end_time}"
            user_start_dt = datetime.strptime(user_start_str, "%Y-%m-%d %H:%M")
            user_end_dt   = datetime.strptime(user_end_str, "%Y-%m-%d %H:%M")

            # Filter out listings that don't fully cover this entire range
            filtered = []
            for listing in all_listings:
                if listing.is_available_for_range(user_start_dt, user_end_dt):
                    filtered.append(listing)
            all_listings = filtered
        except ValueError:
            pass

    context = {
        "listings": all_listings,
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
