from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    #All mentioned below things are built-in variables we are just overridding them 
    # columns shown in user list page
    list_display = ['username', 'email', 'display_name', 'status', 'is_staff']

    # clickable column
    list_display_links = ['username', 'email']

    # filter panel on right side
    list_filter = ['status', 'is_staff', 'is_active']

    # search bar — search by these fields
    search_fields = ['username', 'email', 'display_name']

    # add our custom fields to the existing UserAdmin form
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile', {'fields': ('display_name', 'bio', 'avatar', 'status')}),
    )

    # controls "Edit existing user" form
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('display_name', 'bio', 'avatar', 'status', 'last_seen')}),
    )