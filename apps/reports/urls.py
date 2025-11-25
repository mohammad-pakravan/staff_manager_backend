"""
URLs for reports app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Statistics
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
]

