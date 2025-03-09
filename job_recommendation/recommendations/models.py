from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=255)
    student_id = models.CharField(max_length=50, unique=True)
    grades = models.JSONField(default=dict)  # Store subjects and grades as JSON
    interests = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name



class Job(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_remote = models.BooleanField(default=False)
    job_url = models.URLField()
    source = models.CharField(max_length=50)  # To track which site the job came from
    external_id = models.CharField(max_length=255, blank=True, null=True)  # For deduplication
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['external_id']),
        ]
        
    def __str__(self):
        return f"{self.title} at {self.company}"