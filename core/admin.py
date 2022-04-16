from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.
import core.models

admin.site.register(core.models.User, UserAdmin)