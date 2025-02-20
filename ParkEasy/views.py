from django.shortcuts import render


def user_login(request):
    return render(request, 'login.html')


def park_listings(request):
    return render(request, 'park_listings.html')


def post_parking(request):
    return render(request, 'post_parking.html',)
