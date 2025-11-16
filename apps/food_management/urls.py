from django.urls import path
from . import views

urlpatterns = [
    # Meal Management
    path('meals/', views.MealListCreateView.as_view(), name='meal-list-create'),
    path('meals/<int:pk>/', views.MealDetailView.as_view(), name='meal-detail'),
    path('restaurants/<int:restaurant_id>/meals/', views.restaurant_meals, name='restaurant-meals'),
    
    
    # Meal Options - حذف شد (از DailyMenuMealOption استفاده کنید)
    
    # Restaurants
    path('restaurants/', views.RestaurantListCreateView.as_view(), name='restaurant-list-create'),
    path('restaurants/<int:pk>/', views.RestaurantDetailView.as_view(), name='restaurant-detail'),
    path('admin-food-restaurants/', views.admin_food_restaurants, name='admin-food-restaurants'),
    path('admin-food/meals-by-date/', views.admin_food_meals_by_date, name='admin-food-meals-by-date'),
    path('admin-food/remove-meal-from-menu/', views.admin_food_remove_meal_from_menu, name='admin-food-remove-meal-from-menu'),
    
    # Daily Menus
    path('daily-menus/', views.DailyMenuListView.as_view(), name='daily-menu-list'),
    
    # Food Reservations
    path('reservations/', views.FoodReservationListCreateView.as_view(), name='reservation-list-create'),
    path('reservations/<int:pk>/', views.FoodReservationDetailView.as_view(), name='reservation-detail'),
    path('reservations/<int:reservation_id>/cancel/', views.cancel_reservation, name='cancel-reservation'),
    path('reservations/limits/', views.user_reservation_limits, name='user-reservation-limits'),
    
    # Guest Reservations
    path('guest-reservations/', views.GuestReservationListCreateView.as_view(), name='guest-reservation-list-create'),
    path('guest-reservations/<int:pk>/', views.GuestReservationDetailView.as_view(), name='guest-reservation-detail'),
    path('guest-reservations/<int:reservation_id>/cancel/', views.cancel_guest_reservation, name='cancel-guest-reservation'),
    path('guest-reservations/limits/', views.user_guest_reservation_limits, name='user-guest-reservation-limits'),
    
    # Statistics and Reports
    path('statistics/', views.comprehensive_statistics, name='comprehensive-statistics'),
    path('statistics/simple/', views.meal_statistics, name='meal-statistics'),  # برای سازگاری با کدهای قبلی
    path('statistics/meals-by-restaurant/', views.meal_statistics_by_restaurant, name='meal-statistics-by-restaurant'),
    path('statistics/reservations-by-base-meal/', views.reservations_by_base_meal, name='reservations-by-base-meal'),
    path('statistics/users-by-date-range/', views.user_statistics_by_date_range, name='user-statistics-by-date-range'),
    path('centers/<int:center_id>/reservations/', views.center_reservations, name='center-reservations'),
    path('centers/<int:center_id>/export/excel/', views.export_reservations_excel, name='export-excel'),
    path('centers/<int:center_id>/export/pdf/', views.export_reservations_pdf, name='export-pdf'),
    
    # Detailed Reports
    path('reports/by-meal-option/', views.report_by_meal_option, name='report-by-meal-option'),
    path('reports/by-base-meal/', views.report_by_base_meal, name='report-by-base-meal'),
    path('reports/by-user/', views.report_by_user, name='report-by-user'),
    path('reports/by-date/', views.report_by_date, name='report-by-date'),
    path('reports/comprehensive/', views.comprehensive_report, name='comprehensive-report'),
    path('reports/detailed-reservations/', views.detailed_reservations_report, name='detailed-reservations-report'),
    
    # User Reservations
    path('user/reservations/', views.user_reservations, name='user-reservations'),
    path('user/guest-reservations/', views.user_guest_reservations, name='user-guest-reservations'),
    path('user/reservations/summary/', views.user_reservations_summary, name='user-reservations-summary'),
    
    # Employee Management
    path('employee/daily-menus/', views.employee_daily_menus, name='employee-daily-menus'),
    path('employee/reservations/', views.employee_reservations, name='employee-reservations'),
    path('employee/reservations/<int:reservation_id>/', views.employee_update_reservation, name='employee-update-reservation'),
    path('employee/reservations/<int:reservation_id>/cancel/', views.employee_cancel_reservation, name='employee-cancel-reservation'),
    path('employee/guest-reservations/', views.employee_create_guest_reservation, name='employee-create-guest-reservation'),
    path('employee/guest-reservations/<int:guest_reservation_id>/', views.employee_update_guest_reservation, name='employee-update-guest-reservation'),
    path('employee/guest-reservations/<int:guest_reservation_id>/cancel/', views.employee_cancel_guest_reservation, name='employee-cancel-guest-reservation'),
]

