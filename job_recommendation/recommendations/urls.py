from django.urls import path
from . import views

urlpatterns = [
    path('recommendations/<str:student_id>/', views.get_recommendations, name='get_recommendations'),
]
