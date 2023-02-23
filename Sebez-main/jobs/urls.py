from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.LandingPage.as_view(), name="home"),
    path("search", views.SearchResultsList.as_view(), name="job-search"),
    path("jobs/", views.JobList.as_view(), name="job-list"),
    path("contact/", views.ContactApplication.as_view(), name="ap-contact"),
    path("shortlist/", views.ShortListApplication.as_view(), name="ap-shortlist"),
    path("archive/", views.ArchiveApplication.as_view(), name="ap-archive"),
    path("resume/", views.ResumeBuilder.as_view(), name="resume-builder"),
    path("em/", views.EmployerHomePage.as_view(), name="employer-home"),
    path("em/my-jobs/", views.EmployerMyJobs.as_view(), name="employer-myjobs"),
    path("em/my-drafts/", views.EmployerMyDrafts.as_view(), name="employer-mydrafts"),
    path("em/jobs/new/", views.JobCreate.as_view(), name="job-create"),
    path(
        "em/jobs/<slug:slug>/applicants/",
        views.ApplicantManager.as_view(),
        name="job-applicants",
    ),
    path(
        "jobs/<slug:slug>/applicants/<str:uid>/",
        views.ApplicantDetail.as_view(),
        name="job-applicant-detail",
    ),
    path("jobs/<slug:slug>/", views.JobDetail.as_view(), name="job-detail"),
    path("jobs/<slug:slug>/edit/", views.JobUpdate.as_view(), name="job-update"),
    path("jobs/<slug:slug>/delete/", views.JobDelete.as_view(), name="job-delete"),
    path(
        "jobs/<slug:slug>/apply/", views.SubmitApplication.as_view(), name="job-apply"
    ),
    path("jobs/<slug:slug>/reports/", views.ReportJob.as_view(), name="report"),
    path("category/<slug:slug>/", views.JobCategoryView.as_view(), name="job-category"),
]
