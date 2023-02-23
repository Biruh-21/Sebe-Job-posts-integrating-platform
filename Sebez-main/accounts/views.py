from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import ListView, View

from jobs.models import JobApplication

from .forms import LoginForm, SignupForm, UserUpdateForm, JSProfileUpdateForm
from .models import Account, JobSeeker, Bookmark
from .tokens import email_confirmation_token
from jobs.models import Job
 

def signin(request):
    """Display login form and handle the login process."""
    if request.user.is_authenticated:
        if request.user.account_type == 2:
            return redirect("jobs:employer-home")
        else:
            return redirect("jobs:home")

    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            if user.account_type == 2:
                return redirect("jobs:employer-home")
            else:
                return redirect("jobs:home")
        else:
            messages.error(request, "Invalid Email or Password.")
    login_form = LoginForm()
    context = {"login_form": login_form}
    return render(request, "accounts/login.html", context)


def signout(request):
    """Log the user out."""
    logout(request)
    return redirect("jobs:home")


def signup(request):
    """Display signup form and handle the signup action."""

    if request.method == "POST":
        # the user has submitted the form (POST request): get the data submitted
        signup_form = SignupForm(request.POST)
        if signup_form.is_valid():
            try:
                user = signup_form.save(commit=False)
                user.is_active = False  # until the user confirms the email
                user.save()

                # send verification email
                current_site = get_current_site(request)
                mail_subject = "Verify your email address"
                message = render_to_string(
                    "accounts/confirm_email.html",
                    {
                        "user": user,
                        "domain": current_site.domain,
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "token": email_confirmation_token.make_token(user),
                    },
                )
                to_email = signup_form.cleaned_data.get("email")
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
            except Exception as e:
                print("Error occurred while registering the user: ", e)

            # Set first name to session variable to pass it to another view
            first_name = signup_form.cleaned_data.get("first_name")
            request.session["first_name"] = first_name
            return redirect(to=reverse("accounts:verify"))
    else:
        # it is GET request: display an empty signup form
        signup_form = SignupForm()

    context = {"signup_form": signup_form}
    return render(request, "accounts/signup.html", context)


def activate(request, uidb64, token):
    """Activate the user account after the confirms their email address."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and email_confirmation_token.check_token(user, token):
        user.is_active = True
        user.save()
        # Automatically log the user in up on successful confirmation
        login(request, user)
        messages.success(request, "Your email has been verified successfully.")
        messages.success(
            request, "You can now write posts and share your idea to the world."
        )
        return redirect("jobs:home")
    else:
        return HttpResponse("Confirmation link is invalid.")


def inform_to_verify(request):
    """Inform the user to verify their email while registering."""
    first_name = request.session.get("first_name")
    if first_name:
        context = {"first_name": first_name}
    else:
        context = {"first_name": "User"}
    return render(request, "accounts/verify.html", context=context)


class JobSeekerProfile(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Show profile of job seeker."""

    model = JobSeeker
    template_name = "accounts/job_seeker_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        first_name = self.request.user.first_name
        last_name = self.request.user.last_name
        # First letter of first and last name to be used as profile
        context["profile_pic"] = f"{first_name[0]}{last_name[0]}".upper()
        return context

    def test_func(self):
        # check the user trying to view profile is the owner
        user = get_object_or_404(Account, uid=self.kwargs.get("uid"))
        return self.request.user == user


class SavedJobs(LoginRequiredMixin, ListView):
    """Show saved jobs by the user"""

    model = Job
    context_object_name = "saved_jobs"
    template_name = "accounts/saved_jobs.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        saved_jobs = []
        reported_jobs = []
        if self.request.user.pk is not None:
            user = Account.objects.get(id=self.request.user.pk)
            jobseeker = JobSeeker.objects.get(user=user)
            saved_jobs = [b.job for b in user.bookmark_set.all()]
            reported_jobs = [r.job for r in jobseeker.reports.all()]

        context["saved_jobs"] = saved_jobs
        context["reported_jobs"] = reported_jobs
        return context

    def get_queryset(self):
        user = Account.objects.get(id=self.request.user.pk)
        saved_jobs = [b.job for b in user.bookmark_set.all()]
        return saved_jobs


@login_required
def update_profile(request, uid):
    """Update job seeker profile for authenticated user."""
    # Check if the user is authorized to edit the profile.
    owner = Account.objects.get(uid=uid)
    if request.user == owner:
        # can edit its own profile
        if request.method == "POST":
            user_form = UserUpdateForm(request.POST, instance=request.user)
            profile_form = JSProfileUpdateForm(
                request.POST, request.FILES, instance=request.user.jobseeker
            )
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, "Your account has been updated successfully.")
                return redirect(to=reverse("accounts:js-profile", args=(uid,)))
        else:
            user_form = UserUpdateForm(instance=request.user)
            profile_form = JSProfileUpdateForm(instance=request.user.jobseeker)

        context = {
            "user_form": user_form,
            "profile_form": profile_form,
        }
        return render(request, "accounts/update_js_profile.html", context)
    else:
        # Can't edit others profile
        return HttpResponseForbidden("<h1>403 Forbidden</h1>")


class SubmittedProposals(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Applications submitted by a job seeker. (Only the owner can see)"""

    model = JobApplication
    template_name = "accounts/proposals.html"
    context_object_name = "proposals"
    paginate_by = 10

    # def get_queryset(self):
    #     jobseeker = JobSeeker.objects.get(user=self.request.user)
    #     active = JobApplication.objects.filter(jobseeker=jobseeker, status__lt=3)
    #     archived = JobApplication.objects.filter(jobseeker=jobseeker, status=3)
    #     context["active"] = active
    #     context["archived"] = archived

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jobseeker = JobSeeker.objects.get(user=self.request.user)
        active = JobApplication.objects.filter(jobseeker=jobseeker, status__lt=3)
        archived = JobApplication.objects.filter(jobseeker=jobseeker, status=3)
        context["active"] = active
        context["archived"] = archived
        return context

    def test_func(self):
        # check the user trying to view profile is the owner
        user = get_object_or_404(Account, uid=self.kwargs.get("uid"))
        return self.request.user == user


class BookmarkJob(View):
    """Handle bookmarking job using ajax calls."""

    def post(self, request):
        user = self.request.user
        if user.is_authenticated:
            # bookmark selected job
            job_id = request.POST.get("job_id")
            selected_job = Job.objects.get(pk=job_id)
            is_bookmarked = False  # initial assumption
            bookmark = Bookmark.objects.filter(user=user, job=selected_job).first()
            if bookmark:
                # The user has already saved it, unsave now
                bookmark.delete()
            else:
                # save the bookmark now
                Bookmark.objects.create(user=user, job=selected_job)
                is_bookmarked = True
            return JsonResponse(
                {"is_bookmarked": is_bookmarked, "job_id": job_id}, status=200
            )
        else:
            # Not authenticated
            messages.warning(
                self.request,
                "Login to your account to bookmark jobs.",
            )
            return JsonResponse({"is_bookmarked": False}, status=401)
