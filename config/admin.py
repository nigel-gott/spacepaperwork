from django.contrib import admin


class GroupBasedAdminSite(admin.AdminSite):
    def has_permission(self, request):
        return request.user.is_active and (
            request.user.groups.filter(name="staff").exists() or request.user.is_staff
        )


# override default admin site
admin.site = GroupBasedAdminSite()
