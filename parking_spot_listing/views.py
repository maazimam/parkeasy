from django.shortcuts import render

# Create your views here.  

def post_parking_spot(request):
    return render(request, 'post_parking.html')

def view_parking_spots(request):
    return render(request, 'park_listings.html')

