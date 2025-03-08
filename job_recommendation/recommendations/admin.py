from django.contrib import admin
from .models import Student, Job, Recommendation
import json

class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'student_id', 'display_grades', 'interests', 'skills')
    search_fields = ('name', 'student_id', 'interests', 'skills')
    list_filter = ('interests',)
    ordering = ('student_id',)

    def display_grades(self, obj):
        try:
            grades_dict = json.loads(obj.grades) if isinstance(obj.grades, str) else obj.grades
            if isinstance(grades_dict, dict):
                return ', '.join([f"{k}: {v}" for k, v in grades_dict.items()])
        except json.JSONDecodeError:
            return "Invalid format"
        return "No grades available"

    display_grades.short_description = "Grades"  # Custom column name


class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'required_skills')
    search_fields = ('title', 'required_skills', 'source')
    list_filter = ('source',)

class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('student', 'job', 'score')
    search_fields = ('student__name', 'job__title')
    list_filter = ('score',)
    ordering = ('-score',)

admin.site.register(Student, StudentAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Recommendation, RecommendationAdmin)
