"""
Serializers for food_management app - Legacy compatibility
All serializers have been moved to meals, reservations, and reports apps.
This file maintains backward compatibility by re-exporting from new apps.
"""
# Re-export serializers from new apps for backward compatibility
from apps.meals.serializers import (
    CenterSerializer,
    RestaurantSerializer,
    SimpleRestaurantSerializer,
    BaseMealSerializer,
    DailyMenuMealOptionSerializer,
    BaseMealWithOptionsSerializer,
    DailyMenuSerializer,
    SimpleBaseMealSerializer,
    MealOptionUpdateSerializer,
    DailyMenuMealUpdateSerializer,
    SimpleEmployeeRestaurantSerializer,
    SimpleEmployeeDailyMenuSerializer,
)

from apps.reservations.serializers import (
    FoodReservationSerializer,
    FoodReservationCreateSerializer,
    SimpleFoodReservationSerializer,
    GuestReservationSerializer,
    GuestReservationCreateSerializer,
    SimpleGuestReservationSerializer,
)

from apps.reports.serializers import (
    FoodReportSerializer,
    MealStatisticsSerializer,
    MealOptionReportSerializer,
    BaseMealReportSerializer,
    UserReportSerializer,
    DateReportSerializer,
    DetailedReservationReportSerializer,
    ComprehensiveReportSerializer,
)

# برای سازگاری با کدهای قبلی
from apps.food_management.models import BaseMeal
Meal = BaseMeal

# Alias for backward compatibility
MealSerializer = BaseMealSerializer
