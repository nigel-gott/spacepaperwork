from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *

# Register your models here.
admin.site.register(Fleet)
admin.site.register(FleetType)
admin.site.register(Corp)
admin.site.register(Character)
admin.site.register(System)
admin.site.register(Region)


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('timezone',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('timezone',)}),
    )


admin.site.register(GooseUser, CustomUserAdmin)
