from django.urls import path
from .views import (
    register,
    user_login,
    user_logout,
    verify,
    profile_view,
    change_password,
    password_change_done,
    change_email,
    admin_verify_user,
    user_notifications,
    admin_send_notification,
    admin_sent_notifications,
    debug_notification_counts,  # Add this import
)

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
    path("verify/", verify, name="verify"),
    path("profile/", profile_view, name="profile"),
    # Password change URLs
    path("password_change/", change_password, name="password_change"),
    path("password_change_done/", password_change_done, name="password_change_done"),
    path("email_change/", change_email, name="email_change"),
    # Verification and notification URLs
    path("admin_verify/<int:user_id>/", admin_verify_user, name="admin_verify_user"),
    path("notifications/", user_notifications, name="user_notifications"),
    path(
        "admin/send_notification/",
        admin_send_notification,
        name="admin_send_notification",
    ),
    path(
        "admin/sent_notifications/",
        admin_sent_notifications,
        name="admin_sent_notifications",
    ),
    path(
        "debug_counts/", debug_notification_counts, name="debug_notification_counts"
    ),  # Add this line
]
