from django.urls import path

from . import views

urlpatterns = [
    path("", views.TourListView.as_view(), name="tour_list"),
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("tour/<int:pk>/", views.TourDetailView.as_view(), name="tour_detail"),
    path("booking/new/", views.BookingCreateView.as_view(), name="booking_create"),
    path(
        "booking/success/",
        views.BookingSuccessView.as_view(),
        name="booking_success",
    ),
    path("comment/new/", views.CommentCreateView.as_view(), name="comment_create"),
    path(
        "comment/success/",
        views.CommentSuccessView.as_view(),
        name="comment_success",
    ),
]
