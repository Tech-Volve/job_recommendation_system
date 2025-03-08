from django.contrib import admin

# Register your models here.

from .models import Student, Job, Recommendation

admin.site.register(Student)
admin.site.register(Job)    
admin.site.register(Recommendation)


