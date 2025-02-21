# listings/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ListingForm
from .models import Listing

@login_required
def create_listing(request):
    if request.method == 'POST':
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.user = request.user  # attach the logged-in user
            listing.save()
            return redirect('view_listings')  # redirect to the listings page
    else:
        form = ListingForm()
    
    return render(request, 'listings/create_listing.html', {'form': form})

def view_listings(request):
    all_listings = Listing.objects.all()
    return render(request, 'listings/view_listings.html', {'listings': all_listings})
