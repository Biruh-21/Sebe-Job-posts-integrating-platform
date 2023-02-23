from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.signin, name="login"),
    path("logout/", views.signout, name="logout"),
    path("verify/", views.inform_to_verify, name="verify"),
    path("bookmark/", views.BookmarkJob.as_view(), name="bookmark"),
    path("confirm/<uidb64>/<token>/", views.activate, name="activate"),
    path("<str:uid>/", views.JobSeekerProfile.as_view(), name="js-profile"),
    path("<str:uid>/saved/", views.SavedJobs.as_view(), name="js-saved-jobs"),
    path("<str:uid>/update/", views.update_profile, name="js-profile-update"),
    path(
        "<str:uid>/proposals/", views.SubmittedProposals.as_view(), name="js-proposals"
    ),
    # path("<str:uid>/draft/", views.DraftPostList.as_view(), name="draft"),
    # path("<str:uid>/saved/", views.SavedPostList.as_view(), name="saved"),
]
