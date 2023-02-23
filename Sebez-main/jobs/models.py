from django.db import models
from django.urls import reverse
import django_filters

from common import utils


class JobCategory(models.Model):
    """Main category holding similar jobs together."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = utils.generate_slug(self.__class__, self.name)
        super().save(*args, **kwargs)


class Job(models.Model):
    """A class representing job."""

    EMPLOYMENT_TYPES = [(1, "Full Time"), (2, "Contract"), (3, "Part Time")]
    STATUS = [(0, "Save Draft"), (1, "Publish Now")]
    LEVEL = [(1, "Entry Level"), (2, "Mid Level"), (3, "Senior Level")]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    location = models.CharField(max_length=200, null=True, blank=True)
    # level = models.CharField(max_length=100, blank=True, null=True)
    level = models.SmallIntegerField(
        verbose_name="Experience", choices=LEVEL, blank=True, null=True
    )

    date_posted = models.DateTimeField(auto_now=True)
    deadline = models.DateField(blank=True, null=True)

    source_link = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    summary = models.CharField(max_length=500, blank=True, null=True)

    category = models.ForeignKey(
        JobCategory, on_delete=models.PROTECT, related_name="jobs"
    )
    employer = models.ForeignKey(
        "accounts.Employer", on_delete=models.PROTECT, related_name="jobs"
    )

    job_type = models.SmallIntegerField(choices=EMPLOYMENT_TYPES, default=1)
    status = models.SmallIntegerField(choices=STATUS, default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-date_posted"]

    def save(self, *args, **kwargs):
        """Assign unique slug from job title (only once)."""
        if not self.slug:
            self.slug = utils.generate_slug(self.__class__, self.title)
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Absolute url to job detail"""
        return reverse("jobs:job-detail", kwargs={"slug": self.slug})


class JobFilter(django_filters.FilterSet):
    """Filter jobs based on different parameters"""

    class Meta:
        model = Job
        fields = ["job_type", "level", "location"]


def get_resume_path(instance, filename):
    """Generate a unique name for resume and return its full path."""
    from datetime import date

    extension = filename.split(".")[-1]
    job = instance.job.title
    first_name = instance.jobseeker.user.first_name
    last_name = instance.jobseeker.user.last_name
    applicantlast_name = f"{first_name} {last_name}"
    new_filename = f"{job}_{applicantlast_name}_resume.{extension}"
    image_path = f"resumes/{new_filename}"
    return image_path


class JobApplication(models.Model):
    """Application submitted by a job seeker."""

    APPLICATION_STATUS = (
        (0, "Pending"),
        (1, "Short Listed"),
        (2, "Contacted"),
        (3, "Archived"),
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    jobseeker = models.ForeignKey(
        "accounts.JobSeeker", on_delete=models.CASCADE, related_name="applications"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.SmallIntegerField(choices=APPLICATION_STATUS, default=0)
    resume = models.FileField(
        verbose_name="CV/Resume",
        upload_to=get_resume_path,
        validators=[utils.validate_resume_file_extension],
    )

    def __str__(self):
        full_name = f"{self.jobseeker.user.first_name} {self.jobseeker.user.last_name}"
        return full_name

    class Meta:
        ordering = ["-timestamp"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "jobseeker"], name="unique_application"
            ),
        ]


class Report(models.Model):
    """Report submitted on scam jobs."""

    REPORT_REASONS = (
        (1, "It is offensive, descriminatory"),
        (2, "It seems like a fake job"),
        (3, "Vague description"),
        (4, "Other"),
    )

    job = models.ForeignKey(Job, on_delete=models.DO_NOTHING, related_name="reports")
    user = models.ForeignKey(
        "accounts.JobSeeker", on_delete=models.DO_NOTHING, related_name="reports"
    )
    reason = models.SmallIntegerField(choices=REPORT_REASONS)
    detail = models.TextField(
        verbose_name="Addtional information", blank=True, null=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user} report on {self.job}"

    class Meta:
        ordering = ["-timestamp"]
        constraints = [
            models.UniqueConstraint(fields=["job", "user"], name="unique_report"),
        ]
