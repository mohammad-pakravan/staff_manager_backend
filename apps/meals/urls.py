"""
URLs for meals app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Meal Management
    path('meals/', views.MealListCreateView.as_view(), name='meal-list-create'),
    path('meals/<int:pk>/', views.MealDetailView.as_view(), name='meal-detail'),
    path('restaurants/<int:restaurant_id>/meals/', views.restaurant_meals, name='restaurant-meals'),
    
    # Restaurants
    path('restaurants/', views.RestaurantListCreateView.as_view(), name='restaurant-list-create'),
    path('restaurants/<int:pk>/', views.RestaurantDetailView.as_view(), name='restaurant-detail'),
    path('admin-food-restaurants/', views.admin_food_restaurants, name='admin-food-restaurants'),
    path('admin-food/meals-by-date/', views.admin_food_meals_by_date, name='admin-food-meals-by-date'),
    path('admin-food/remove-meal-from-menu/', views.admin_food_remove_meal_from_menu, name='admin-food-remove-meal-from-menu'),
    
    # Daily Menus
    path('daily-menus/', views.DailyMenuListView.as_view(), name='daily-menu-list'),
    
    # Dessert Management
    path('desserts/', views.DessertListCreateView.as_view(), name='dessert-list-create'),
    path('desserts/<int:pk>/', views.DessertDetailView.as_view(), name='dessert-detail'),
    path('restaurants/<int:restaurant_id>/desserts/', views.restaurant_desserts, name='restaurant-desserts'),
    path('admin-food/desserts-by-date/', views.admin_food_desserts_by_date, name='admin-food-desserts-by-date'),
    path('admin-food/remove-dessert-from-menu/', views.admin_food_remove_dessert_from_menu, name='admin-food-remove-dessert-from-menu'),
]

