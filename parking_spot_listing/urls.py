from django.urls import path
from .views import post_parking_spot, view_parking_spots

urlpatterns = [
    path('post/', post_parking_spot, name='post_parking'),
    path('spots/', view_parking_spots, name='view_spots'),
]
