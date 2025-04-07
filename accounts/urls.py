from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import register, user_login, user_logout, verify, profile_view, change_password, password_change_done, change_email
from . import views

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
    path("verify/", verify, name="verify"),
    path("profile/", profile_view, name="profile"),
    
    # Password change URLs - Custom implementation (Option 2)
    path("password_change/", change_password, name="password_change"),
    path("password_change_done/", password_change_done, name="password_change_done"),
    path("email_change/", change_email, name="email_change"),
]
