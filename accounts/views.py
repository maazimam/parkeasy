from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    PasswordChangeForm,
)
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .forms import EmailChangeForm
from django.contrib import messages

# Import the messaging model and User to send admin notifications.
from messaging.models import Message
from django.contrib.auth.models import User


def home(request):
    return redirect("view_listings")


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log in the user after registration
            return redirect("home")  # Redirect to homepage
    else:
        form = UserCreationForm()
    return render(request, "accounts/register.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")  # Redirect to homepage
    else:
        form = AuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})


def user_logout(request):
    logout(request)
    return redirect("login")  # Redirect to login page after logout


def verify(request):
    """
    Handles account verification requests.
    When the correct answer is provided, a message is sent to every admin user,
    including a link to the user's profile in the admin panel.
    The user does not view the message content but receives a notification that
    the verification request has been sent for review.
    """
    if request.user.profile.is_verified:
        return render(request, "accounts/verify.html", {"success": True})

    context = {}
    if request.method == "POST":
        answer = request.POST.get("answer")
        verification_file = request.FILES.get("verification_file")

        # Validate that the file is a PDF if provided.
        if verification_file and not verification_file.name.lower().endswith(".pdf"):
            context["error_message"] = "Only PDF files are allowed."
            return render(request, "accounts/verify.html", context)

        if answer == "ParkEasy":
            # Save verification file if provided.
            if verification_file:
                request.user.profile.verification_file = verification_file
                request.user.profile.save()

            # Build link to the admin profile change page.
            profile_link = f"http://127.0.0.1:8000/admin/accounts/profile/{request.user.profile.id}/change/"

            # Send a message to all admin users.
            admin_users = User.objects.filter(is_staff=True)
            for admin in admin_users:
                Message.objects.create(
                    sender=request.user,
                    recipient=admin,
                    subject="Verification Request",
                    body=f"User {request.user.username} has requested verification. "
                    f"Please review their profile here: {profile_link}",
                )

            # Inform the user that the verification request has been sent.
            messages.info(
                request,
                "Your verification request has been sent for review. You will be notified once it is approved.",
            )
            return render(request, "accounts/verify.html", {"success": True})
        else:
            context["error_message"] = (
                "Incorrect answer, verification failed. Please try again."
            )

    return render(request, "accounts/verify.html", context)


@login_required
def profile_view(request):
    # Get messages from session if present
    success_message = request.session.pop("success_message", None)
    error_message = request.session.pop("error_message", None)

    # Render the user's profile page with message context
    return render(
        request,
        "accounts/profile.html",
        {
            "user": request.user,
            "success_message": success_message,
            "error_message": error_message,
        },
    )


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Prevent user from being logged out.
            update_session_auth_hash(request, user)
            return redirect("password_change_done")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "accounts/password_change.html", {"form": form})


@login_required
def password_change_done(request):
    request.session["success_message"] = "Password changed successfully!"
    return redirect("profile")


@login_required
def change_email(request):
    # Determine if the user is adding a new email.
    is_adding_email = request.user.email == "" or request.user.email is None

    if request.method == "POST":
        form = EmailChangeForm(request.POST, user=request.user)
        if form.is_valid():
            request.user.email = form.cleaned_data["email"]
            request.user.save()

            if is_adding_email:
                request.session["success_message"] = "Email added successfully!"
            else:
                request.session["success_message"] = "Email updated successfully!"

            return redirect("profile")
    else:
        form = EmailChangeForm(user=request.user)

    return render(
        request,
        "accounts/change_email.html",
        {"form": form, "is_adding_email": is_adding_email},
    )
