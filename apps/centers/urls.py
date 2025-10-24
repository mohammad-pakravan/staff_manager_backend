from django.urls import path
from . import views

urlpatterns = [
    path('', views.CenterListCreateView.as_view(), name='center-list-create'),
    path('<int:pk>/', views.CenterDetailView.as_view(), name='center-detail'),
    path('<int:center_id>/employees/', views.center_employees, name='center-employees'),
]


