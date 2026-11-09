"""
Модели стартапа «Конные туры».

В проекте нарочно показаны все три вида связей между таблицами:

- один-к-одному  : Client <-> ClientProfile
- один-ко-многим : Category -> Tour (и Tour/Client -> Comment, Booking)
- многие-ко-многим: Client <-> Tour через промежуточную модель Booking
  (понадобилась промежуточная модель, а не обычный ManyToManyField,
  потому что у связи "клиент купил тур" есть свои поля — дата и время).
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class Client(models.Model):
    """Клиент турфирмы — человек, который может бронировать туры и оставлять комментарии."""

    full_name = models.CharField("ФИО", max_length=200)
    email = models.EmailField("Email", unique=True)
    phone = models.CharField("Телефон", max_length=20)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name


class ClientProfile(models.Model):
    """
    Дополнительный профиль клиента — связь один-к-одному с Client.

    Вынесен в отдельную таблицу, т.к. эти данные (паспорт, дата рождения,
    экстренный контакт) нужны не при каждом обращении к клиенту, а только
    при оформлении конкретного тура.
    """

    client = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Клиент",
    )
    passport_number = models.CharField("Номер паспорта", max_length=20)
    birth_date = models.DateField("Дата рождения")
    emergency_contact = models.CharField(
        "Контакт на случай ЧС", max_length=200, blank=True
    )

    class Meta:
        verbose_name = "Профиль клиента"
        verbose_name_plural = "Профили клиентов"

    def __str__(self):
        return f"Профиль клиента: {self.client.full_name}"


class Category(models.Model):
    """Категория тура, например «конный», «пеший», «мото»."""

    name = models.CharField("Название", max_length=100, unique=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tour(models.Model):
    """
    Тур — конкретное предложение турфирмы.

    Связь с категорией — один-ко-многим: у одной категории может быть
    много туров, но у каждого тура ровно одна категория.
    """

    title = models.CharField("Название", max_length=200)
    description = models.TextField("Описание", blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="tours",
        verbose_name="Категория",
    )
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    duration_hours = models.PositiveSmallIntegerField("Длительность, ч")

    # Многие-ко-многим с клиентами через Booking (нужны поля дата/время
    # у самой связи, поэтому через промежуточную модель, а не напрямую).
    clients = models.ManyToManyField(
        Client,
        through="Booking",
        related_name="tours",
        verbose_name="Клиенты",
    )

    class Meta:
        verbose_name = "Тур"
        verbose_name_plural = "Туры"
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("tour_detail", kwargs={"pk": self.pk})


class Booking(models.Model):
    """
    Бронирование тура клиентом на конкретные дату и время.

    Это промежуточная модель связи многие-ко-многим между Client и Tour.

    Бизнес-правило: один клиент может купить только один тур на
    определённые дату и время — он физически не может быть на двух турах
    одновременно. Правило реализовано ограничением уникальности по
    (client, date, time): какой бы тур клиент ни выбрал, второй раз
    забронировать что-либо на то же дата+время не получится.
    """

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Клиент",
    )
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Тур",
    )
    date = models.DateField("Дата")
    time = models.TimeField("Время")
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ["-date", "-time"]
        constraints = [
            models.UniqueConstraint(
                fields=["client", "date", "time"],
                name="unique_client_booking_per_datetime",
            )
        ]

    def __str__(self):
        return f"{self.client} → {self.tour} ({self.date} {self.time})"


class Comment(models.Model):
    """
    Комментарий клиента к туру.

    Клиент может оставить несколько комментариев к турам, на которых он
    был, поэтому здесь нет ограничения уникальности. Единственное
    правило — комментировать можно только тур, на который у клиента есть
    хотя бы одно бронирование (проверяется в clean(), а значит и в любой
    ModelForm на основе этой модели).
    """

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Клиент",
    )
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Тур",
    )
    text = models.TextField("Текст комментария")
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.client} о «{self.tour}»"

    def clean(self):
        if self.client_id and self.tour_id:
            has_booking = Booking.objects.filter(
                client_id=self.client_id, tour_id=self.tour_id
            ).exists()
            if not has_booking:
                raise ValidationError(
                    "Оставлять комментарий можно только к туру, "
                    "на который есть бронирование этого клиента."
                )
