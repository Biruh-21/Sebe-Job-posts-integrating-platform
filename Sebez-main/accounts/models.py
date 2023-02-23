from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from common import utils


class AccountManager(BaseUserManager):
    """A User manager for a custom user model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, first_name, last_name, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        if not first_name:
            raise ValueError("Users must have first name.")
        if not last_name:
            raise ValueError("Users must have last name.")

        email = self.normalize_email(email)
        user = self.model(
            email=email, first_name=first_name, last_name=last_name, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, first_name, last_name, password=None, **extrafields):
        extrafields.setdefault("is_staff", False)
        extrafields.setdefault("is_superuser", False)
        return self._create_user(email, first_name, last_name, password, **extrafields)

    def create_superuser(
        self, email, first_name, last_name, password=None, **extrafields
    ):
        extrafields.setdefault("is_staff", True)
        extrafields.setdefault("is_admin", True)
        extrafields.setdefault("is_superuser", True)

        if extrafields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extrafields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self._create_user(email, first_name, last_name, password, **extrafields)


class Account(AbstractUser):
    """
    A class implementing a fully featured custom User model with
    admin-compliant permissions.

    first_name, last_name, email and password are required.
    """

    ACCOUNT_TYPES = (
        (1, "Job Seeker"),
        (2, "Employer"),
    )

    username = None
    email = models.EmailField("email", max_length=200, unique=True)
    first_name = models.CharField(verbose_name="First Name", max_length=150)
    last_name = models.CharField(verbose_name="Last Name", max_length=150)
    uid = models.CharField("UID", max_length=12)
    is_admin = models.BooleanField(default=False)
    account_type = models.SmallIntegerField(
        verbose_name="Account Type", choices=ACCOUNT_TYPES, default=1
    )

    objects = AccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "account_type"]

    class Meta:
        verbose_name = "account"
        verbose_name_plural = "accounts"
        constraints = [
            models.UniqueConstraint(
                fields=["email", "account_type"], name="unique_account"
            )
        ]

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs):
        """Assign unique UID before saving the user."""
        if not self.uid:
            self.uid = utils.generate_uid(self.__class__)
        return super().save(*args, **kwargs)


def get_resume_path(instance, filename):
    """Generate a unique name for resume and return its full path."""
    from datetime import date

    extension = filename.split(".")[-1]
    first_name = instance.user.first_name
    last_name = instance.user.last_name
    new_filename = f"{first_name}_{last_name}_resume.{extension}"
    image_path = f"resumes/{new_filename}"
    return image_path


class JobSeeker(models.Model):
    """Job seeker profile."""

    PROFILE_VISIBILITY = ((0, "Private"), (1, "Public"))
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    resume = models.FileField(
        verbose_name="CV/Resume",
        upload_to=get_resume_path,
        blank=True,
        null=True,
        validators=[utils.validate_resume_file_extension],
    )
    visibility = models.SmallIntegerField(
        verbose_name="Resume visibility",
        choices=PROFILE_VISIBILITY,
        default=0,
    )

    def __str__(self):
        return self.user.get_full_name()


class Employer(models.Model):
    """Employer: An individual or company that post job offers."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employer_profile",
    )
    company_name = models.CharField(max_length=200)
    about = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True, max_length=250)

    class Meta:
        verbose_name = "employer"
        verbose_name_plural = "employers"

    def __str__(self) -> str:
        return self.company_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = utils.generate_slug(self.__class__, self.company_name)
        super().save(*args, **kwargs)


class Bookmark(models.Model):
    """Save Job posts for later reading."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    job = models.ForeignKey("jobs.Job", on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "job"], name="unique_bookmark")
        ]


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_save_profile(sender, instance, created, **kwargs):
    """
    Automatically create a user profile after sign up or
    update it whenever user information is updated.
    """

    if instance.account_type == 1:
        # Job seeker account
        if created:
            JobSeeker.objects.create(user=instance)
        else:
            instance.jobseeker.save()

    elif instance.account_type == 2:
        # Employer account
        if created:
            Employer.objects.create(user=instance)
        else:
            instance.employer_profile.save()
        pass
