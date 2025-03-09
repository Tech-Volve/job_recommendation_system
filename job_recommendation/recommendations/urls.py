from django.urls import path
from . import views

urlpatterns = [
    path('recommendations/<str:student_id>/', views.get_recommendations, name='get_recommendations'),
    path('', views.home, name='home'),
    path('recommend/', views.recommendation_page, name='recommend_page'),
    path('login/', views.login, name='login' )
]
