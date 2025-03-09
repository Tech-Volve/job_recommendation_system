from django.urls import path
from . import views
from .views import StoreJobsView

urlpatterns = [
    path('recommendations/<str:student_id>/', views.get_recommendations, name='get_recommendations'),
    path('', views.home, name='home'),
    path('recommend/', views.recommendation_page, name='recommend_page'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    # path('logout/', views.logout, name='logout'),
    path('org/signup/', views.org_signup, name='org_signup'),
    path('org/login/', views.org_login, name='org_login'),
    path('org/dashboard/', views.org_dashboard, name='org_dashboard'),
    path('user-dashboard/', views.user_dashboard, name='user-dashboard'),
    path('api/store-jobs/', StoreJobsView.as_view(), name='store-jobs'),
    
]
