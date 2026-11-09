from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # Автодокументация Django: /admin/doc/ (нужен вход как суперпользователь)
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("", include("tours.urls")),
]
