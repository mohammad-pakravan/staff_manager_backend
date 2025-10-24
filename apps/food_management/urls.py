from django.urls import path
from . import views

urlpatterns = [
    # Meal Management
    path('meals/', views.MealListCreateView.as_view(), name='meal-list-create'),
    path('meals/<int:pk>/', views.MealDetailView.as_view(), name='meal-detail'),
    
    # Meal Types
    path('meal-types/', views.MealTypeListView.as_view(), name='meal-type-list'),
    
    # Weekly Menus
    path('weekly-menus/', views.WeeklyMenuListCreateView.as_view(), name='weekly-menu-list-create'),
    path('weekly-menus/<int:pk>/', views.WeeklyMenuDetailView.as_view(), name='weekly-menu-detail'),
    
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
    path('statistics/', views.meal_statistics, name='meal-statistics'),
    path('centers/<int:center_id>/reservations/', views.center_reservations, name='center-reservations'),
    path('centers/<int:center_id>/export/excel/', views.export_reservations_excel, name='export-excel'),
    path('centers/<int:center_id>/export/pdf/', views.export_reservations_pdf, name='export-pdf'),
    
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

