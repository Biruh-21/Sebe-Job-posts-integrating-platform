from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Account, Employer, JobSeeker


@admin.register(Account)
class AccountAdmin(UserAdmin):
    """Admin for a custom user model with no username field."""

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "password1",
                    "password2",
                    "account_type",
                ),
            },
        ),
    )
    list_display = ("email", "first_name", "last_name", "account_type", "is_active")
    list_filter = ("account_type", "is_active")
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("last_login", "date_joined")
    ordering = ("first_name", "last_name")


@admin.register(JobSeeker)
class JobSeekerAdmin(admin.ModelAdmin):
    list_display = ("user", "resume", "visibility")


@admin.register(Employer)
class EmpoyerAdmin(admin.ModelAdmin):
    list_display = ("user", "company_name")
    prepopulated_fields = {"slug": ["company_name"]}
