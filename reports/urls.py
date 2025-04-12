from django.urls import path
from . import views

urlpatterns = [
    path(
        "<str:content_type_str>/<int:object_id>/", views.report_item, name="report_item"
    ),
]
