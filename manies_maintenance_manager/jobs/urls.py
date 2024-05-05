from django.urls import path

from .views import job_list

app_name = "jobs"
urlpatterns = [
    path("", job_list, name="job_list"),
]
