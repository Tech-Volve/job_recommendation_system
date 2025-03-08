from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=255)
    student_id = models.CharField(max_length=50, unique=True)
    grades = models.JSONField()  # Store subjects and grades as JSON
    interests = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Job(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    required_skills = models.TextField()
    source = models.CharField(max_length=255, blank=True, null=True)  # API source

    def __str__(self):
        return self.title

class Recommendation(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    score = models.FloatField()  # Confidence score

    def __str__(self):
        return f"{self.student.name} -> {self.job.title}"
