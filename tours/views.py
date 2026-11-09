"""Вьюхи стартапа «Конные туры»: просмотр каталога и отправка данных (брони/комментарии)."""

from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from .forms import BookingForm, CommentForm
from .models import Booking, Category, Comment, Tour


class TourListView(ListView):
    """Список всех туров с указанием категории и цены."""

    model = Tour
    template_name = "tours/tour_list.html"
    context_object_name = "tours"


class TourDetailView(DetailView):
    """Детальная страница тура: описание и оставленные к нему комментарии."""

    model = Tour
    template_name = "tours/tour_detail.html"
    context_object_name = "tour"


class CategoryListView(ListView):
    """Список категорий туров (конный / пеший / мото и т.д.) с числом туров в каждой."""

    model = Category
    template_name = "tours/category_list.html"
    context_object_name = "categories"


class BookingCreateView(CreateView):
    """
    Страница оформления бронирования тура.

    При отправке некорректных данных (в частности — повторная бронь того
    же клиента на уже занятые дату и время) форма возвращается на экран
    с ошибкой, объект Booking не создаётся.
    """

    model = Booking
    form_class = BookingForm
    template_name = "tours/booking_form.html"
    success_url = reverse_lazy("booking_success")


class CommentCreateView(CreateView):
    """
    Страница добавления комментария к туру.

    Отклоняет отправку, если у клиента нет бронирования на выбранный тур.
    """

    model = Comment
    form_class = CommentForm
    template_name = "tours/comment_form.html"
    success_url = reverse_lazy("comment_success")


class BookingSuccessView(TemplateView):
    """Страница-подтверждение успешного бронирования."""

    template_name = "tours/booking_success.html"


class CommentSuccessView(TemplateView):
    """Страница-подтверждение успешной отправки комментария."""

    template_name = "tours/comment_success.html"
