"""
Тесты стартапа «Конные туры».

Структура:
- OneToOneRelationTests        — связь один-к-одному (Client <-> ClientProfile)
- CategoryTourRelationTests     — связь один-ко-многим (Category -> Tour)
- BookingManyToManyTests        — связь многие-ко-многим (Client <-> Tour
                                   через Booking) + бизнес-правило
                                   «1 клиент — 1 тур на дату и время»
- CommentBusinessRuleTests       — правило «комментировать можно только то,
                                   на что было бронирование», и что одному
                                   клиенту можно оставить несколько
                                   комментариев
- ViewSubmissionTests            — тестирование отправки данных через формы
                                   (views): успешные и отклонённые случаи
"""

import datetime

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Booking, Category, Client, ClientProfile, Comment, Tour


def make_client(full_name="Иван Иванов", email="ivan@example.com", phone="+996700000000"):
    return Client.objects.create(full_name=full_name, email=email, phone=phone)


def make_category(name="Конный"):
    return Category.objects.create(name=name)


def make_tour(category, title="Тур в горы", price="5000.00", duration_hours=3):
    return Tour.objects.create(
        title=title,
        description="Описание тура",
        category=category,
        price=price,
        duration_hours=duration_hours,
    )


class OneToOneRelationTests(TestCase):
    """Связь один-к-одному: Client <-> ClientProfile."""

    def setUp(self):
        self.client_obj = make_client()

    def test_profile_linked_to_client(self):
        profile = ClientProfile.objects.create(
            client=self.client_obj,
            passport_number="AN1234567",
            birth_date=datetime.date(1990, 5, 20),
        )
        self.assertEqual(profile.client, self.client_obj)

    def test_client_can_access_profile_via_related_name(self):
        ClientProfile.objects.create(
            client=self.client_obj,
            passport_number="AN1234567",
            birth_date=datetime.date(1990, 5, 20),
        )
        self.assertEqual(self.client_obj.profile.passport_number, "AN1234567")

    def test_creating_second_profile_for_same_client_raises_integrity_error(self):
        ClientProfile.objects.create(
            client=self.client_obj,
            passport_number="AN1234567",
            birth_date=datetime.date(1990, 5, 20),
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ClientProfile.objects.create(
                    client=self.client_obj,
                    passport_number="AN7654321",
                    birth_date=datetime.date(1991, 1, 1),
                )
        # после ошибки у клиента остаётся ровно один профиль
        self.assertEqual(ClientProfile.objects.filter(client=self.client_obj).count(), 1)


class CategoryTourRelationTests(TestCase):
    """Связь один-ко-многим: Category -> Tour."""

    def setUp(self):
        self.category = make_category()

    def test_category_has_multiple_tours(self):
        make_tour(self.category, title="Тур 1")
        make_tour(self.category, title="Тур 2")
        self.assertEqual(self.category.tours.count(), 2)

    def test_tour_belongs_to_single_category(self):
        tour = make_tour(self.category)
        self.assertEqual(tour.category, self.category)

    def test_deleting_category_with_tours_is_protected(self):
        make_tour(self.category)
        with self.assertRaises(ProtectedError):
            self.category.delete()
        # категория и тур остались на месте
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())


class BookingManyToManyTests(TestCase):
    """
    Связь многие-ко-многим: Client <-> Tour через Booking.

    И бизнес-правило: один клиент может купить только один тур на
    определённые дату и время.
    """

    def setUp(self):
        self.category = make_category()
        self.client_obj = make_client()
        self.other_client = make_client(
            full_name="Пётр Петров", email="petr@example.com", phone="+996700000001"
        )
        self.tour = make_tour(self.category, title="Конная прогулка")
        self.other_tour = make_tour(self.category, title="Пеший поход")
        self.date = datetime.date(2026, 7, 1)
        self.time = datetime.time(10, 0)

    def test_client_can_book_multiple_tours(self):
        Booking.objects.create(
            client=self.client_obj, tour=self.tour, date=self.date, time=self.time
        )
        Booking.objects.create(
            client=self.client_obj,
            tour=self.other_tour,
            date=self.date,
            time=datetime.time(15, 0),
        )
        self.assertEqual(self.client_obj.tours.count(), 2)

    def test_tour_can_be_booked_by_multiple_clients(self):
        Booking.objects.create(
            client=self.client_obj, tour=self.tour, date=self.date, time=self.time
        )
        Booking.objects.create(
            client=self.other_client, tour=self.tour, date=self.date, time=self.time
        )
        self.assertEqual(self.tour.clients.count(), 2)

    def test_client_tours_related_manager_returns_booked_tours(self):
        Booking.objects.create(
            client=self.client_obj, tour=self.tour, date=self.date, time=self.time
        )
        self.assertIn(self.tour, self.client_obj.tours.all())

    def test_duplicate_booking_same_datetime_same_tour_raises_integrity_error(self):
        Booking.objects.create(
            client=self.client_obj, tour=self.tour, date=self.date, time=self.time
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Booking.objects.create(
                    client=self.client_obj,
                    tour=self.tour,
                    date=self.date,
                    time=self.time,
                )
        self.assertEqual(Booking.objects.filter(client=self.client_obj).count(), 1)

    def test_duplicate_booking_same_datetime_different_tour_raises_integrity_error(self):
        """Клиент не может оказаться одновременно на двух РАЗНЫХ турах."""
        Booking.objects.create(
            client=self.client_obj, tour=self.tour, date=self.date, time=self.time
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Booking.objects.create(
                    client=self.client_obj,
                    tour=self.other_tour,
                    date=self.date,
                    time=self.time,
                )
        self.assertEqual(Booking.objects.filter(client=self.client_obj).count(), 1)

    def test_same_client_can_book_same_tour_on_different_datetime(self):
        Booking.objects.create(
            client=self.client_obj, tour=self.tour, date=self.date, time=self.time
        )
        Booking.objects.create(
            client=self.client_obj,
            tour=self.tour,
            date=self.date,
            time=datetime.time(16, 0),
        )
        self.assertEqual(Booking.objects.filter(client=self.client_obj).count(), 2)

    def test_different_clients_can_book_same_tour_same_datetime(self):
        """Ограничение уникальности — по клиенту, поэтому разных клиентов оно не трогает."""
        Booking.objects.create(
            client=self.client_obj, tour=self.tour, date=self.date, time=self.time
        )
        Booking.objects.create(
            client=self.other_client, tour=self.tour, date=self.date, time=self.time
        )
        self.assertEqual(Booking.objects.filter(date=self.date, time=self.time).count(), 2)


class CommentBusinessRuleTests(TestCase):
    """Комментировать можно только тур, на который есть бронирование; несколько — можно."""

    def setUp(self):
        self.category = make_category()
        self.client_obj = make_client()
        self.tour = make_tour(self.category, title="Конная прогулка")
        self.other_tour = make_tour(self.category, title="Пеший поход")

    def _book(self, tour, time=datetime.time(10, 0)):
        return Booking.objects.create(
            client=self.client_obj,
            tour=tour,
            date=datetime.date(2026, 7, 1),
            time=time,
        )

    def test_comment_allowed_when_booking_exists(self):
        self._book(self.tour)
        comment = Comment(client=self.client_obj, tour=self.tour, text="Отличный тур!")
        comment.full_clean()  # не должно бросить исключение
        comment.save()
        self.assertEqual(Comment.objects.count(), 1)

    def test_comment_rejected_without_booking(self):
        comment = Comment(client=self.client_obj, tour=self.tour, text="Хочу отзыв оставить")
        with self.assertRaises(ValidationError):
            comment.full_clean()
        self.assertEqual(Comment.objects.count(), 0)

    def test_client_can_leave_multiple_comments_on_same_tour(self):
        self._book(self.tour)
        Comment.objects.create(client=self.client_obj, tour=self.tour, text="Комментарий 1")
        Comment.objects.create(client=self.client_obj, tour=self.tour, text="Комментарий 2")
        self.assertEqual(
            Comment.objects.filter(client=self.client_obj, tour=self.tour).count(), 2
        )

    def test_client_can_comment_on_several_booked_tours(self):
        self._book(self.tour)
        self._book(self.other_tour, time=datetime.time(15, 0))
        Comment.objects.create(client=self.client_obj, tour=self.tour, text="Про первый тур")
        Comment.objects.create(
            client=self.client_obj, tour=self.other_tour, text="Про второй тур"
        )
        self.assertEqual(Comment.objects.filter(client=self.client_obj).count(), 2)


class ViewSubmissionTests(TestCase):
    """Тестирование отправки данных через формы/вьюхи: успешные и отклонённые случаи."""

    def setUp(self):
        self.category = make_category()
        self.client_obj = make_client()
        self.tour = make_tour(self.category, title="Конная прогулка")
        self.other_tour = make_tour(self.category, title="Пеший поход")

    # ---------- страницы чтения ----------

    def test_tour_list_status_200_and_template(self):
        response = self.client.get(reverse("tour_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tours/tour_list.html")

    def test_tour_detail_shows_comments(self):
        Booking.objects.create(
            client=self.client_obj,
            tour=self.tour,
            date=datetime.date(2026, 7, 1),
            time=datetime.time(10, 0),
        )
        Comment.objects.create(client=self.client_obj, tour=self.tour, text="Прекрасно!")
        response = self.client.get(reverse("tour_detail", kwargs={"pk": self.tour.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Прекрасно!")

    def test_category_list_status_200(self):
        response = self.client.get(reverse("category_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.category.name)

    # ---------- бронирование (создание данных) ----------

    def test_booking_create_view_get_status_200(self):
        response = self.client.get(reverse("booking_create"))
        self.assertEqual(response.status_code, 200)

    def test_booking_create_view_valid_post_creates_booking_and_redirects(self):
        response = self.client.post(
            reverse("booking_create"),
            {
                "client": self.client_obj.pk,
                "tour": self.tour.pk,
                "date": "2026-07-01",
                "time": "10:00",
            },
        )
        self.assertRedirects(response, reverse("booking_success"))
        self.assertEqual(Booking.objects.count(), 1)

    def test_booking_create_view_duplicate_post_is_rejected(self):
        Booking.objects.create(
            client=self.client_obj,
            tour=self.tour,
            date=datetime.date(2026, 7, 1),
            time=datetime.time(10, 0),
        )
        response = self.client.post(
            reverse("booking_create"),
            {
                "client": self.client_obj.pk,
                "tour": self.other_tour.pk,
                "date": "2026-07-01",
                "time": "10:00",
            },
        )
        # форма возвращается с ошибкой, редиректа на success нет
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertEqual(Booking.objects.count(), 1)

    # ---------- комментарии (создание данных) ----------

    def test_comment_create_view_valid_post_creates_comment_and_redirects(self):
        Booking.objects.create(
            client=self.client_obj,
            tour=self.tour,
            date=datetime.date(2026, 7, 1),
            time=datetime.time(10, 0),
        )
        response = self.client.post(
            reverse("comment_create"),
            {
                "client": self.client_obj.pk,
                "tour": self.tour.pk,
                "text": "Очень понравилось",
            },
        )
        self.assertRedirects(response, reverse("comment_success"))
        self.assertEqual(Comment.objects.count(), 1)

    def test_comment_create_view_without_booking_is_rejected(self):
        response = self.client.post(
            reverse("comment_create"),
            {
                "client": self.client_obj.pk,
                "tour": self.tour.pk,
                "text": "Пытаюсь оставить без брони",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertEqual(Comment.objects.count(), 0)
