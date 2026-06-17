from django.urls import path
from .views import simulate_makeup

urlpatterns = [
    path('simulate/makeup/', simulate_makeup, name='simulate-makeup'),
]
