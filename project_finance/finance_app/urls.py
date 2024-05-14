from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('', views.front_page_view, name='frontpage'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='finance_app/login.html'), name='login'),
    path('logout/', views.LogoutView, name = 'logout'),
]
