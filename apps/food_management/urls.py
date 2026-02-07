"""
URLs for food_management app - Legacy compatibility
All views have been moved to meals, reservations, and reports apps.
This file maintains backward compatibility by redirecting to new apps.
"""
from django.urls import path
from apps.meals import views as meals_views
from apps.reservations import views as reservations_views
from apps.reports import views as reports_views

urlpatterns = [
    # Meal Management - Redirected to meals app
    path('meals/', meals_views.MealListCreateView.as_view(), name='meal-list-create'),
    path('meals/<int:pk>/', meals_views.MealDetailView.as_view(), name='meal-detail'),
    path('restaurants/<int:restaurant_id>/meals/', meals_views.restaurant_meals, name='restaurant-meals'),
    
    # Restaurants - Redirected to meals app
    path('restaurants/', meals_views.RestaurantListCreateView.as_view(), name='restaurant-list-create'),
    path('restaurants/<int:pk>/', meals_views.RestaurantDetailView.as_view(), name='restaurant-detail'),
    path('admin-food-restaurants/', meals_views.admin_food_restaurants, name='admin-food-restaurants'),
    path('admin-food/meals-by-date/', meals_views.admin_food_meals_by_date, name='admin-food-meals-by-date'),
    path('admin-food/remove-meal-from-menu/', meals_views.admin_food_remove_meal_from_menu, name='admin-food-remove-meal-from-menu'),
    
    # Daily Menus - Redirected to meals app
    path('daily-menus/', meals_views.DailyMenuListView.as_view(), name='daily-menu-list'),
    
    # Food Reservations - Redirected to reservations app
    path('reservations/', reservations_views.FoodReservationListCreateView.as_view(), name='reservation-list-create'),
    path('reservations/<int:pk>/', reservations_views.FoodReservationDetailView.as_view(), name='reservation-detail'),
    path('reservations/<int:reservation_id>/cancel/', reservations_views.cancel_reservation, name='cancel-reservation'),
    path('reservations/limits/', reservations_views.user_reservation_limits, name='user-reservation-limits'),
    
    # Guest Reservations - Redirected to reservations app
    path('guest-reservations/', reservations_views.GuestReservationListCreateView.as_view(), name='guest-reservation-list-create'),
    path('guest-reservations/<int:pk>/', reservations_views.GuestReservationDetailView.as_view(), name='guest-reservation-detail'),
    path('guest-reservations/<int:reservation_id>/cancel/', reservations_views.cancel_guest_reservation, name='cancel-guest-reservation'),
    path('guest-reservations/limits/', reservations_views.user_guest_reservation_limits, name='user-guest-reservation-limits'),
    
    # Statistics and Reports - Redirected to reports app
    path('statistics/', reports_views.comprehensive_statistics, name='comprehensive-statistics'),
    path('statistics/simple/', reports_views.meal_statistics, name='meal-statistics'),  # برای سازگاری با کدهای قبلی
    path('statistics/meals-by-restaurant/', reports_views.meal_statistics_by_restaurant, name='meal-statistics-by-restaurant'),
    path('statistics/reservations-by-base-meal/', reports_views.reservations_by_base_meal, name='reservations-by-base-meal'),
    path('statistics/users-by-date-range/', reports_views.user_statistics_by_date_range, name='user-statistics-by-date-range'),
    path('centers/<int:center_id>/reservations/', reports_views.center_reservations, name='center-reservations'),
    path('centers/<int:center_id>/export/excel/', reports_views.export_reservations_excel, name='export-excel'),
    path('centers/<int:center_id>/export/pdf/', reports_views.export_reservations_pdf, name='export-pdf'),
    
    # Detailed Reports - Redirected to reports app
    path('reports/by-meal-option/', reports_views.report_by_meal_option, name='report-by-meal-option'),
    path('reports/by-base-meal/', reports_views.report_by_base_meal, name='report-by-base-meal'),
    path('reports/by-user/', reports_views.report_by_user, name='report-by-user'),
    path('reports/by-date/', reports_views.report_by_date, name='report-by-date'),
    path('reports/comprehensive/', reports_views.comprehensive_report, name='comprehensive-report'),
    path('reports/detailed-reservations/', reports_views.detailed_reservations_report, name='detailed-reservations-report'),
    
    # User Reservations - Redirected to reservations app
    path('user/reservations/', reservations_views.user_reservations, name='user-reservations'),
    path('user/guest-reservations/', reservations_views.user_guest_reservations, name='user-guest-reservations'),
    path('user/reservations/summary/', reservations_views.user_reservations_summary, name='user-reservations-summary'),
    
    # Employee Management - Redirected to reservations app
    path('employee/daily-menus/', reservations_views.employee_daily_menus, name='employee-daily-menus'),
    path('employee/reservations/', reservations_views.employee_reservations, name='employee-reservations'),
    path('employee/reservations/<int:reservation_id>/', reservations_views.employee_update_reservation, name='employee-update-reservation'),
    path('employee/reservations/<int:reservation_id>/cancel/', reservations_views.employee_cancel_reservation, name='employee-cancel-reservation'),
    path('employee/guest-reservations/', reservations_views.employee_create_guest_reservation, name='employee-create-guest-reservation'),
    path('employee/guest-reservations/<int:guest_reservation_id>/', reservations_views.employee_update_guest_reservation, name='employee-update-guest-reservation'),
    path('employee/guest-reservations/<int:guest_reservation_id>/cancel/', reservations_views.employee_cancel_guest_reservation, name='employee-cancel-guest-reservation'),



    # Food Admin Forget  Reservations
    path("forget/reservations/<int:pk>" , meals_views.admin_food_forget_reservations , name= "admin-food-forget-eservations")
]

