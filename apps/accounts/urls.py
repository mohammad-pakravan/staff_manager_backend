from django.urls import path
from . import views

urlpatterns = [
 
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('refresh/', views.refresh_token_view, name='token_refresh'),
    path('me/', views.me_view, name='me'),
    path('users/', views.UserListCreateView.as_view(), name='user-list-create'),

    # GET: List all gatherings
    # POST: Create new gathering
    path('gatherings/', views.GatheringListCreateView.as_view(), name='gathering-list-create'),
    
    # GET: Retrieve specific gathering
    # PUT: Update specific gathering
    # PATCH: Partial update specific gathering
    # DELETE: Delete specific gathering
    path('gatherings/export', views.ExportAllGatheringsView.as_view(), name='gathering-detail'),
]


