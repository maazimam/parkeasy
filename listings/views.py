# listings/views.py

from django.shortcuts import render, redirect, get_object_or_404
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

def manage_listings(request):
    owner_listings = Listing.objects.filter(user=request.user)
    return render(request, 'listings/manage_listings.html', {'listings': owner_listings})

@login_required
def edit_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)
    if request.method == "POST":
        form = ListingForm(request.POST, instance=listing)
        if form.is_valid():
            form.save()
            return redirect("manage_listings")
    else: 
        form = ListingForm(instance= listing)
    
    return render(request, 'listings/edit_listing.html', {'form': form})

@login_required
def delete_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, user=request.user)
    if request.method == 'POST':
        listing.delete()
        return redirect('manage_listings')
    
    return render(request, 'listings/confirm_delete.html', {'listing': listing})

        