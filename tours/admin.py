from django.contrib import admin

from .models import Booking, Category, Client, ClientProfile, Comment, Tour

admin.site.register(Client)
admin.site.register(ClientProfile)
admin.site.register(Category)
admin.site.register(Tour)
admin.site.register(Booking)
admin.site.register(Comment)
