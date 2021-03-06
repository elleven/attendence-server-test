# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from models import User

# Register your models here.


class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'jobnumber', 'userid', 'attendence_id', 'email', 'department_id', 'workplace', 'is_delete')
    search_fields = ('jobnumber', 'name')
    list_filter = ('is_delete', )


admin.site.register(User, UserAdmin)
