from django.contrib import admin
from .models import Student, Job
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


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'is_remote', 'created_at')
    list_filter = ('is_remote', 'source', 'created_at')
    search_fields = ('title', 'company', 'location', 'description')
    date_hierarchy = 'created_at'


# class RecommendationAdmin(admin.ModelAdmin):
#     list_display = ('student', 'job', 'score')
#     search_fields = ('student__name', 'job__title')
#     list_filter = ('score',)
#     ordering = ('-score',)

admin.site.register(Student, StudentAdmin)

# admin.site.register(Recommendation, RecommendationAdmin)
