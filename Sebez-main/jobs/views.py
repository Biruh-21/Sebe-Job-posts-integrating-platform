from imp import source_from_cache
from re import template
from urllib import request
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    DeleteView,
    View,
)
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy

from accounts.models import Employer, JobSeeker, Account

from .models import Job, JobApplication, JobCategory, JobFilter, Report


class LandingPage(View):
    """Show landing page of the website"""

    def get(self, request):
        if request.user.is_authenticated:
            # TODO: redirect to different pages based on account type
            if request.user.account_type == 2:
                return redirect(to=reverse("jobs:employer-home"))
            else:
                return redirect(to=reverse("jobs:job-list"))

        latest_jobs = Job.objects.all()[:10]
        popular_categories = JobCategory.objects.all()[:6]
        return render(
            request,
            "jobs/index.html",
            context={
                "latest_jobs": latest_jobs,
                "popular_categories": popular_categories,
            },
        )


class JobDetail(DetailView):
    """Show the detail of a single post."""

    model = Job
    template_name = "jobs/job_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = (
            Job.objects.select_related("category")
            .select_related("employer")
            .get(slug=self.kwargs["slug"])
        )
        applicants = [
            application.jobseeker.user
            for application in JobApplication.objects.filter(job=job)
        ]
        context["job"] = job
        context["applicants"] = applicants
        return context


class JobList(ListView):
    """Show the list of jobs."""

    template_name = "jobs/job_list.html"
    context_object_name = "jobs"
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

        queryset = self.get_queryset()
        filter = JobFilter(self.request.GET, queryset=queryset)
        context["filter"] = filter
        context["saved_jobs"] = saved_jobs
        context["reported_jobs"] = reported_jobs
        return context

    def get_queryset(self):
        all_jobs = (
            Job.objects.select_related("category")
            .select_related("employer")
            .filter(status=1)
        )
        filter = JobFilter(self.request.GET, queryset=all_jobs)
        return filter.qs


class JobCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Display job creation form and handle the process."""

    model = Job
    fields = [
        "category",
        "title",
        "description",
        "location",
        "deadline",
        "job_type",
        "level",
        "status",
    ]
    template_name = "jobs/job_create.html"

    def form_valid(self, form):
        # assign the current logged in user as author of the post
        employer = Employer.objects.get(user=self.request.user)
        form.instance.employer = employer
        if form.instance.status == 0:
            msg = "Your post has been saved as draft."
        elif form.instance.status == 1:
            msg = "Your post has been published."
        messages.success(self.request, msg)
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.account_type == 2


class JobUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Show job update form and handle the process."""

    model = Job
    fields = [
        "category",
        "title",
        "description",
        "location",
        "deadline",
        "job_type",
        "level",
        "status",
    ]
    template_name = "jobs/job_update.html"

    def form_valid(self, form):
        # assign the current logged in user as author of the post
        employer = Employer.objects.get(user=self.request.user)
        form.instance.employer = employer
        if form.instance.status == 0:
            msg = "Your post has been saved as draft."
        elif form.instance.status == 1:
            msg = "Your post has been published."
        messages.success(self.request, msg)
        return super().form_valid(form)

    def test_func(self):
        # check that the person trying to update the job is the  owner
        employer = Employer.objects.get(user=self.request.user)
        return self.get_object().employer == employer


class JobDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Show job deletion form and handle the process."""

    model = Job
    template_name = "jobs/job_delete.html"

    def get_success_url(self):
        # After deleting the job, redirect to employer home page
        messages.info(self.request, "Your job has been deleted.")
        return reverse("jobs:employer-myjobs")

    def test_func(self):
        # check that the person trying to delete the job is the  owner
        employer = Employer.objects.get(user=self.request.user)
        return self.get_object().employer == employer


class EmployerHomePage(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Show employer's home page."""

    model = Job
    template_name = "jobs/employer_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employer = Employer.objects.get(user=self.request.user)
        published_jobs = Job.objects.filter(
            employer=employer, status=1, source_link=None
        )
        draft_jobs = Job.objects.filter(employer=employer, status=0)
        context["published_jobs"] = published_jobs
        context["draft_jobs"] = draft_jobs
        return context

    def test_func(self):
        return self.request.user.account_type == 2


class EmployerMyJobs(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Show all jobs posted by the employer."""

    model = Job
    context_object_name = "employer_jobs"
    template_name = "jobs/employer_myjobs.html"

    def get_queryset(self):
        employer = Employer.objects.get(user=self.request.user)
        return Job.objects.filter(employer=employer, status=1, source_link=None)

    def test_func(self):
        return self.request.user.account_type == 2


class EmployerMyDrafts(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Show all jobs posted by the employer."""

    model = Job
    context_object_name = "employer_jobs"
    template_name = "jobs/employer_mydrafts.html"

    def get_queryset(self):
        employer = Employer.objects.get(user=self.request.user)
        return Job.objects.filter(employer=employer, status=0, source_link=None)

    def test_func(self):
        return self.request.user.account_type == 2


class ApplicantManager(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Show all applicants for the job and manage them."""

    model = JobApplication
    context_object_name = "applications"
    template_name = "jobs/applicants.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = Job.objects.get(slug=self.kwargs["slug"])
        active = JobApplication.objects.filter(job=job, status__lt=3)
        short_listed = JobApplication.objects.filter(job=job, status=1)
        contacted = JobApplication.objects.filter(job=job, status=2)
        archived = JobApplication.objects.filter(job=job, status=3)
        context["job"] = job
        context["active"] = active
        context["short_listed"] = short_listed
        context["contacted"] = contacted
        context["archived"] = archived
        return context

    def test_func(self):
        return self.request.user.account_type == 2


class ApplicantDetail(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Show detail of a job application."""

    model = Job
    context_object_name = "application"
    template_name = "jobs/applicant_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = Job.objects.get(slug=self.kwargs["slug"])
        jobseeker = JobSeeker.objects.get(user__uid=self.kwargs["uid"])
        first_name = jobseeker.user.first_name
        last_name = jobseeker.user.last_name
        application = JobApplication.objects.get(job=job, jobseeker=jobseeker)
        context["profile_pic"] = f"{first_name[0]}{last_name[0]}"
        context["application"] = application
        # context["job"] = job
        return context

    def test_func(self):
        return self.request.user.account_type == 2


class SubmitApplication(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Show job application form and handle the process."""

    model = JobApplication
    template_name = "jobs/application_form.html"
    fields = ["resume"]

    def form_valid(self, form):
        job = Job.objects.get(slug=self.kwargs["slug"])
        form.instance.job = job
        # assign the current logged in user as applicant
        jobseeker = JobSeeker.objects.get(user=self.request.user)
        form.instance.jobseeker = jobseeker
        messages.success(self.request, "Your applicant has been submitted!")
        return super().form_valid(form)

        # return reverse_lazy("accounts:js-proposals", args=(jobseeker.user.uid,))

    def get_success_url(self):
        # After deleting the job, redirect to employer home page
        jobseeker = JobSeeker.objects.get(user=self.request.user)
        return reverse_lazy("accounts:js-proposals", args=(jobseeker.user.uid,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = Job.objects.get(slug=self.kwargs["slug"])
        context["job"] = job
        return context

    def test_func(self):
        return self.request.user.account_type == 1


class SearchResultsList(ListView):
    """Show the list of search results."""

    model = Job
    context_object_name = "search_results"
    template_name = "jobs/search_result.html"

    def get_queryset(self):
        # query entered by the user
        self.query = self.request.GET["q"]
        self.location = self.request.GET["l"]

        search_vector = SearchVector("title", "description", "location")
        search_query = SearchQuery(f"{self.query} {self.location}")
        self.search_results = (
            Job.objects.annotate(
                search=search_vector, rank=SearchRank(search_vector, search_query)
            )
            .filter(search=search_query)
            .order_by("-rank")
        )
        self.total = len(self.search_results)
        paginator = Paginator(self.search_results, 10)  # 10 jobs per page
        page = self.request.GET.get("page", 1)
        try:
            self.search_results = paginator.page(page)
        except PageNotAnInteger:
            self.search_results = paginator.page(1)
        except EmptyPage:
            self.search_results = paginator.page(paginator.num_pages)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.query
        context["location"] = self.location
        context["search_results"] = self.search_results
        context["total"] = self.total
        return context


class JobCategoryView(ListView):
    """Show all post in a certain category."""

    model = Job
    template_name = "jobs/category.html"
    context_object_name = "category_jobs"
    paginate_by = 10
    filterset_class = JobFilter

    def get_queryset(self):
        all_jobs = (
            Job.objects.select_related("category")
            .select_related("employer")
            .filter(category__slug=self.kwargs.get("slug"))
        )
        filter = JobFilter(self.request.GET, queryset=all_jobs)
        return filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        saved_jobs = []
        reported_jobs = []
        if self.request.user.pk is not None:
            user = Account.objects.get(id=self.request.user.pk)
            jobseeker = JobSeeker.objects.get(user=user)
            saved_jobs = [b.job for b in user.bookmark_set.all()]
            reported_jobs = [r.job for r in jobseeker.reports.all()]

        queryset = self.get_queryset()
        filter = JobFilter(self.request.GET, queryset=queryset)
        context["filter"] = filter
        context["saved_jobs"] = saved_jobs
        context["reported_jobs"] = reported_jobs
        context["total"] = len(queryset)
        return context


class ReportJob(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Handle job reporting using ajax calls."""

    model = Report
    fields = ["reason", "detail"]
    template_name = "jobs/report.html"

    def form_valid(self, form):
        # assign user and job for the report
        job = Job.objects.get(slug=self.kwargs["slug"])
        jobseeker = JobSeeker.objects.get(user=self.request.user)
        form.instance.user = jobseeker
        form.instance.job = job
        return super().form_valid(form)

    def get_success_url(self):
        messages.info(self.request, "Your report has been recorded.")
        return reverse("jobs:job-list")

    def test_func(self):
        return self.request.user.account_type == 1

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = Job.objects.get(slug=self.kwargs["slug"])
        context["job"] = job
        return context


class ShortListApplication(View):
    """Handle short listing application using ajax calls."""

    def post(self, request):
        user = self.request.user
        if user.is_authenticated:
            # bookmark selected job
            ap_id = request.POST.get("ap_id")
            application = JobApplication.objects.get(id=ap_id)
            if application.status == 0:
                application.status = 1
                messages.info(self.request, "Application short listed")
            else:
                application.status = 0
            application.save()
            return JsonResponse({"ap_id": ap_id}, status=200)
        else:
            # Not authenticated
            messages.warning(
                self.request,
                "Login to your account to perform this action",
            )
            return JsonResponse({"is_contacted": False}, status=401)


class ContactApplication(View):
    """Handle contact application using ajax calls."""

    def post(self, request):
        user = self.request.user
        if user.is_authenticated:
            # bookmark selected job
            ap_id = request.POST.get("ap_id")
            application = JobApplication.objects.get(id=ap_id)
            if application.status == 0:
                application.status = 2
                messages.info(self.request, "Application moved to contacted list")
            else:
                application.status = 0
            application.save()
            return JsonResponse({"ap_id": ap_id}, status=200)
        else:
            # Not authenticated
            messages.warning(
                self.request,
                "Login to your account to perform this action",
            )
            return JsonResponse({"is_contacted": False}, status=401)


class ArchiveApplication(View):
    """Handle archiving application using ajax calls."""

    def post(self, request):
        user = self.request.user
        if user.is_authenticated:
            # bookmark selected job
            ap_id = request.POST.get("ap_id")
            application = JobApplication.objects.get(id=ap_id)
            if application.status == 0:
                application.status = 3
                messages.info(self.request, "Application archived")
            else:
                application.status = 0
            application.save()
            return JsonResponse({"ap_id": ap_id}, status=200)
        else:
            # Not authenticated
            messages.warning(
                self.request,
                "Login to your account to perform this action",
            )
            return JsonResponse({"is_contacted": False}, status=401)


class ResumeBuilder(LoginRequiredMixin, View):
    """Show resume builder template and handle the process."""

    def get(self, request):
        return render(request, "jobs/resume.html")
