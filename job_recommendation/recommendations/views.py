from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from .job_recommendation import recommend_jobs

def get_recommendations(request, student_id):
    """ API to get job recommendations for a student """
    recommendations = recommend_jobs(student_id)
    return JsonResponse({"student_id": student_id, "recommended_jobs": recommendations})




def home(request):
    return render(request, 'home.html')