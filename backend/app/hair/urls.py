from django.urls import path
from .views import simulate_hair

urlpatterns = [
    path('simulate/hair/', simulate_hair, name='simulate-hair'),
]
