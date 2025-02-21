# listings/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('create_listing/', views.create_listing, name='create_listing'),
    path('view_listings/', views.view_listings, name='view_listings'),
]
