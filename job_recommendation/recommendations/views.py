from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from .job_recommendation import recommend_jobs

def get_recommendations(request, student_id):
    """ API to get job recommendations for a student """
    recommendations = recommend_jobs(student_id)
    return JsonResponse({"student_id": student_id, "recommended_jobs": recommendations})


def recommendation_page(request):
    """ Renders the page where students enter their ID """
    return render(request, 'recommend.html')

def home(request):
    return render(request, 'index.html')

def login(request):
    return render (request, 'login.html')

def signup(request):
    return render (request, 'register.html')

def org_signup(request):
    return render (request, 'org/register-organization.html')

def org_login(request):
    return render (request, 'org/login_organization.html')