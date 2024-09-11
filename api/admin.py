from django.contrib import admin

from .models import Department, NaacFile, User
# Register your models here.
admin.site.register([Department, NaacFile, User])