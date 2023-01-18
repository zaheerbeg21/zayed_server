from django.contrib import admin
from .models import *


class DepartmentAdminUserValues(admin.ModelAdmin):
    list_display = ('id', 'user', 'usertype', 'department')


admin.site.register(Report)
admin.site.register(DepartmentAdminUser, DepartmentAdminUserValues)
admin.site.register(Department)
admin.site.register(UserType)
admin.site.register(Upload)
admin.site.register(Tag)


