from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from .job_recommendation import recommend_jobs
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Job


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

def org_dashboard(request):
    return render (request, 'org/org-dashboard.html')

def user_dashboard(request):
    return render (request, 'dashboard.html')


# In your Django app's views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Job
from .serializers import JobSerializer

class StoreJobsView(APIView):
    def post(self, request):
        jobs_data = request.data.get('jobs', [])
        stored_jobs = []
        
        for job_data in jobs_data:
            # Create a unique identifier to avoid duplicates
            external_id = f"{job_data.get('source')}_{job_data.get('job_url')}"
            
            # Check if job already exists
            existing_job = Job.objects.filter(external_id=external_id).first()
            
            if existing_job:
                # Update existing job
                serializer = JobSerializer(existing_job, data=job_data, partial=True)
            else:
                # Create new job
                job_data['external_id'] = external_id
                serializer = JobSerializer(data=job_data)
                
            if serializer.is_valid():
                job = serializer.save()
                stored_jobs.append(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        return Response({
            'message': f'Successfully stored {len(stored_jobs)} jobs',
            'jobs': stored_jobs
        }, status=status.HTTP_201_CREATED)