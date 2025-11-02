from django.urls import path
from . import views

urlpatterns = [
 
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('refresh/', views.refresh_token_view, name='token_refresh'),
    path('me/', views.me_view, name='me'),
]


