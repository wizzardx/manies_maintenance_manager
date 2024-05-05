from django.shortcuts import render


def job_list(request):
    return render(request, "pages/job_list.html")
