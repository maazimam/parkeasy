from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


def home(request):
    return render(request, "home.html")


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log in the user after registration
            return redirect("home")  # Redirect to homepage (update as needed)
    else:
        form = UserCreationForm()
    return render(request, "accounts/register.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")  # Redirect to homepage (update as needed)
    else:
        form = AuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})


def user_logout(request):
    logout(request)
    return redirect("login")  # Redirect to login page after logout

from django.shortcuts import render, redirect
from django.contrib import messages

def verify(request):
    if request.method == "POST":
        # Replace with your actual question logic. For now, assume the correct answer is "42"
        answer = request.POST.get("answer")
        if answer == "ParkEasy":
            # Mark user as verified
            request.user.profile.is_verified = True
            request.user.profile.save()
            messages.success(request, "Your account has been verified!")
            return redirect("create_listing")  # or wherever you want to redirect verified users
        else:
            messages.error(request, "Incorrect answer. Please try again.")
    return render(request, "accounts/verify.html")
