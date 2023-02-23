from django.contrib import admin

from .models import Job, JobCategory, JobApplication, Report


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["title", "employer", "date_posted", "deadline", "category"]
    list_filter = ["category", "date_posted", "deadline"]
    search_fields = ["title", "description"]
    prepopulated_fields = {"slug": ["title"]}


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    prepopulated_fields = {"slug": ["name"]}
    ordering = ["name"]
    search_fields = ["name"]


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ["jobseeker", "job", "timestamp", "status"]
    list_filter = ["status"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["job", "user", "reason", "timestamp"]
    list_filter = ["reason"]
