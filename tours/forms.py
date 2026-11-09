"""Формы для отправки данных: бронирование тура и комментарий к туру."""

from django import forms

from .models import Booking, Comment


class BookingForm(forms.ModelForm):
    """
    Форма бронирования тура.

    Уникальность связки (клиент, дата, время) проверяется автоматически
    средствами ModelForm (validate_unique вызывается в is_valid()),
    поэтому повторная попытка забронировать клиенту что-либо на уже
    занятые дату и время провалит валидацию формы без обращения к базе
    напрямую из view.
    """

    class Meta:
        model = Booking
        fields = ["client", "tour", "date", "time"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time": forms.TimeInput(attrs={"type": "time"}),
        }


class CommentForm(forms.ModelForm):
    """
    Форма комментария к туру.

    Правило «комментировать можно только тур, на который есть
    бронирование» задано в Comment.clean() и автоматически подхватывается
    формой: ModelForm вызывает full_clean() связанного объекта при
    is_valid(), так что отдельно дублировать проверку здесь не нужно.
    """

    class Meta:
        model = Comment
        fields = ["client", "tour", "text"]
        widgets = {"text": forms.Textarea(attrs={"rows": 4})}
