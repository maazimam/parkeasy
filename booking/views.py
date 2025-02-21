# booking/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .models import Booking
from .forms import BookingForm
from listings.models import Listing

@login_required
def book_listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    if request.method == 'POST':
        form = BookingForm(request.POST, listing=listing)
        if form.is_valid():
            booking_date = form.cleaned_data['booking_date']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']

            # Validate that the selected times are within the listing's available times
            if start_time < listing.available_time_from or end_time > listing.available_time_until or end_time <= start_time:
                form.add_error(None, 'Please choose a time within the available range and ensure end time is after start time.')
            else:
                # Calculate the booking duration in hours
                duration = (datetime.combine(booking_date, end_time) - datetime.combine(booking_date, start_time)).total_seconds() / 3600
                total_price = float(listing.rent_per_hour) * duration

                booking = Booking(
                    user=request.user,
                    listing=listing,
                    booking_date=booking_date,
                    start_time=start_time,
                    end_time=end_time,
                    total_price=total_price,
                )
                booking.save()
                return redirect('my_bookings')
    else:
        form = BookingForm(listing=listing)
    
    return render(request, 'booking/book_listing.html', {'form': form, 'listing': listing})


@login_required
def my_bookings(request):
    """
    Shows all bookings made by the current logged-in user.
    """
    user_bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'booking/my_bookings.html', {'bookings': user_bookings})

@login_required
def cancel_booking(request, booking_id):
    """
    Optional: Allows a user to cancel (delete) a booking.
    """
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    booking.delete()
    return redirect('my_bookings')
