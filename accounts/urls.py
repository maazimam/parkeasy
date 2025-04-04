from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import register, user_login, user_logout, verify, profile_view
from . import views

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
    path("verify/", verify, name="verify"),
    path("profile/", profile_view, name="profile"),
    
    # Password change URLs
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/accounts/password_change_done/'
    ), name='password_change'),
    path('password_change_done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
]
