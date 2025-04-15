from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    PasswordChangeForm,
)
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import EmailChangeForm, VerificationForm  # Update import

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
    Collects user information for verification and sends a notification to admins.
    Prevents users from submitting multiple verification requests.
    """
    # If already verified, show success page
    if request.user.profile.is_verified:
        return render(request, "accounts/verify.html", {"success": True})

    # If verification already requested but not approved yet, show pending status
    if request.user.profile.verification_requested:
        return render(request, "accounts/verify.html", {"pending": True})

    if request.method == "POST":
        form = VerificationForm(request.POST, request.FILES)
        if form.is_valid():
            # Update user profile with form data
            profile = request.user.profile
            profile.age = form.cleaned_data["age"]
            profile.address = form.cleaned_data["address"]
            profile.phone_number = form.cleaned_data["phone_number"]

            # Save verification file if provided
            verification_file = form.cleaned_data["verification_file"]
            if verification_file:
                profile.verification_file = verification_file

            # Mark verification as requested
            profile.verification_requested = True
            profile.save()

            # Build links for admin actions
            base_url = request.build_absolute_uri("/").rstrip("/")
            verify_link = f"{base_url}/accounts/admin_verify/{request.user.id}/"
            admin_profile_link = (
                f"{base_url}/admin/accounts/profile/{request.user.profile.id}/change/"
            )

            # Send a message to all admin users
            admin_users = User.objects.filter(is_staff=True)
            for admin in admin_users:
                Message.objects.create(
                    sender=request.user,
                    recipient=admin,
                    subject="Verification Request",
                    body=f"User {request.user.username} has requested verification.\n\n"
                    f"User Information:\n"
                    f"- Age: {profile.age}\n"
                    f"- Address: {profile.address}\n"
                    f"- Phone: {profile.phone_number}\n\n"
                    f"Click here to verify the user: {verify_link}\n\n"
                    f"Or view their profile in the admin panel: {admin_profile_link}",
                )

            # Return a confirmation page
            context = {
                "request_sent": True,
                "success_message": "Your verification request has been sent for review. \
                    You will be notified once it is approved.",
            }
            return render(request, "accounts/verify.html", context)
    else:
        form = VerificationForm()

    return render(request, "accounts/verify.html", {"form": form})


@login_required
def admin_verify_user(request, user_id):
    """
    View for administrators to verify users directly from notification messages.
    This creates a smoother workflow than requiring admins to navigate to the admin panel.
    Shows the verification file (if any) before approval.
    """
    # Check if the current user is an admin
    if not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to verify users.")

    # Get the user to verify
    user_to_verify = get_object_or_404(User, pk=user_id)

    # Check if user is already verified
    if user_to_verify.profile.is_verified:
        return render(
            request,
            "accounts/admin_verify.html",
            {"already_verified": True, "username": user_to_verify.username},
        )

    if request.method == "POST" and "confirm_verification" in request.POST:
        # Process verification approval
        user_to_verify.profile.is_verified = True
        user_to_verify.profile.save()

        # Send a confirmation message to the verified user
        Message.objects.create(
            sender=request.user,
            recipient=user_to_verify,
            subject="Account Verification Approved",
            body="Congratulations! Your account has been verified. You can now post parking spots on ParkEasy.",
        )

        # Show confirmation page
        return render(
            request,
            "accounts/admin_verify.html",
            {"verification_complete": True, "username": user_to_verify.username},
        )

    # Show verification details and confirmation form
    return render(
        request,
        "accounts/admin_verify.html",
        {
            "user_to_verify": user_to_verify,
            "has_verification_file": bool(user_to_verify.profile.verification_file),
        },
    )


@login_required
def user_notifications(request):
    """
    Display notification messages for the user, including verification status updates
    """
    # Get all messages sent to this user
    messages_list = Message.objects.filter(recipient=request.user).order_by(
        "-created_at"
    )

    # Mark all as read
    unread_messages = messages_list.filter(read=False)
    unread_messages.update(read=True)

    return render(request, "accounts/notifications.html", {"messages": messages_list})


@login_required
def profile_view(request):
    # Get messages from session if present
    success_message = request.session.pop("success_message", None)
    error_message = request.session.pop("error_message", None)

    # Calculate unread message count for the user
    unread_count = Message.objects.filter(recipient=request.user, read=False).count()

    # Render the user's profile page with message context
    return render(
        request,
        "accounts/profile.html",
        {
            "user": request.user,
            "success_message": success_message,
            "error_message": error_message,
            "unread_count": unread_count,
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
