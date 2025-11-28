"""
URLs for reservations app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Food Reservations
    path('reservations/', views.FoodReservationListCreateView.as_view(), name='reservation-list-create'),
    path('reservations/<int:pk>/', views.FoodReservationDetailView.as_view(), name='reservation-detail'),
    path('reservations/<int:reservation_id>/cancel/', views.cancel_reservation, name='cancel-reservation'),
    path('reservations/limits/', views.user_reservation_limits, name='user-reservation-limits'),
    
    # Combined Reservations (Food + Dessert)
    path('combined-reservations/', views.combined_reservation_create, name='combined-reservation-create'),
    
    # Guest Reservations
    path('guest-reservations/', views.GuestReservationListCreateView.as_view(), name='guest-reservation-list-create'),
    path('guest-reservations/<int:pk>/', views.GuestReservationDetailView.as_view(), name='guest-reservation-detail'),
    path('guest-reservations/<int:reservation_id>/cancel/', views.cancel_guest_reservation, name='cancel-guest-reservation'),
    path('guest-reservations/limits/', views.user_guest_reservation_limits, name='user-guest-reservation-limits'),
    
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
    
    # Dessert Reservations
    path('dessert-reservations/', views.DessertReservationListCreateView.as_view(), name='dessert-reservation-list-create'),
    path('dessert-reservations/<int:pk>/', views.DessertReservationDetailView.as_view(), name='dessert-reservation-detail'),
    path('dessert-reservations/<int:reservation_id>/cancel/', views.cancel_dessert_reservation, name='cancel-dessert-reservation'),
    path('dessert-reservations/limits/', views.user_dessert_reservation_limits, name='user-dessert-reservation-limits'),
    
    # Guest Dessert Reservations
    path('guest-dessert-reservations/', views.GuestDessertReservationListCreateView.as_view(), name='guest-dessert-reservation-list-create'),
    path('guest-dessert-reservations/<int:pk>/', views.GuestDessertReservationDetailView.as_view(), name='guest-dessert-reservation-detail'),
    path('guest-dessert-reservations/<int:reservation_id>/cancel/', views.cancel_guest_dessert_reservation, name='cancel-guest-dessert-reservation'),
    path('guest-dessert-reservations/limits/', views.user_guest_dessert_reservation_limits, name='user-guest-dessert-reservation-limits'),
    
    # User Dessert Reservations
    path('user/dessert-reservations/', views.user_dessert_reservations, name='user-dessert-reservations'),
    path('user/guest-dessert-reservations/', views.user_guest_dessert_reservations, name='user-guest-dessert-reservations'),
    
    # Employee Dessert Management
    path('employee/dessert-reservations/', views.employee_dessert_reservations, name='employee-dessert-reservations'),
    path('employee/dessert-reservations/<int:reservation_id>/', views.employee_update_dessert_reservation, name='employee-update-dessert-reservation'),
    path('employee/dessert-reservations/<int:reservation_id>/cancel/', views.employee_cancel_dessert_reservation, name='employee-cancel-dessert-reservation'),
    path('employee/guest-dessert-reservations/', views.employee_create_guest_dessert_reservation, name='employee-create-guest-dessert-reservation'),
    path('employee/guest-dessert-reservations/<int:guest_reservation_id>/', views.employee_update_guest_dessert_reservation, name='employee-update-guest-dessert-reservation'),
    path('employee/guest-dessert-reservations/<int:guest_reservation_id>/cancel/', views.employee_cancel_guest_dessert_reservation, name='employee-cancel-guest-dessert-reservation'),
]

