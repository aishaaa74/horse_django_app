# Конные туры — учебный стартап (Django)

Django-проект турфирмы с тремя видами связей между моделями, бизнес-правилами
и тестами на уровне моделей и отправки данных (форм/вьюх). Документация —
через встроенное приложение `django.contrib.admindocs`.

## Связи между моделями

| Вид связи        | Модели                          | Как реализовано |
|---|---|---|
| один-к-одному     | `Client` ↔ `ClientProfile`      | `OneToOneField` |
| один-ко-многим    | `Category` → `Tour`             | `ForeignKey` (`on_delete=PROTECT`) |
| многие-ко-многим  | `Client` ↔ `Tour`               | `ManyToManyField(..., through="Booking")` |

`Comment` и `Booking` также содержат обычные `ForeignKey` на `Client` и `Tour`
(ещё по одной связи один-ко-многим каждая).

## Бизнес-правила

- **Один клиент может купить только один тур на определённые дату и время.**
  Реализовано ограничением уникальности `UniqueConstraint(fields=["client",
  "date", "time"])` в модели `Booking` — клиент не может оказаться
  одновременно на двух турах, даже если это два разных тура.
- **Клиент может оставить несколько комментариев к турам, на которых он был.**
  `Comment.clean()` проверяет, что у клиента есть хотя бы одно бронирование
  на этот тур; ограничения на количество комментариев нет.
- **У тура есть категория** (конный / пеший / мото и т.п.) — `Category` с
  `ForeignKey` от `Tour`; удалить категорию, пока у неё есть туры, нельзя
  (`PROTECT`).

## Установка и запуск

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

pip install -r requirements.txt

python manage.py makemigrations tours
python manage.py migrate
python manage.py createsuperuser   # нужен для /admin/ и /admin/doc/
python manage.py runserver
```

Страницы:
- `/` — список туров
- `/categories/` — категории
- `/booking/new/` — форма бронирования
- `/comment/new/` — форма комментария
- `/admin/` — админка
- `/admin/doc/` — автодокументация (django.contrib.admindocs), собранная
  из docstring'ов моделей, форм и вьюх

## Тесты

```bash
python manage.py test tours -v 2
```

Тесты сгруппированы по смыслу в `tours/tests.py`:
- `OneToOneRelationTests` — связь один-к-одному
- `CategoryTourRelationTests` — связь один-ко-многим
- `BookingManyToManyTests` — связь многие-ко-многим + правило «1 тур на
  дату/время»
- `CommentBusinessRuleTests` — правило по комментариям
- `ViewSubmissionTests` — отправка данных через формы (успешные и
  отклонённые случаи)

## Отчёт по тестам в Word

```bash
python generate_report.py
```

Создаст `django_test_report.docx` с полным списком тестов, их docstring'ами
и исходным кодом — для сдачи в качестве отчёта.

## Примечание

Этот код был написан и проверен вручную без доступа к интернету в рабочей
среде — здесь не было возможности установить Django и реально прогнать
`manage.py test`. Логика многократно перепроверена по исходному коду, но
обязательно прогоните тесты у себя перед сдачей и напишите, если что-то
не пройдёт — поправим.
