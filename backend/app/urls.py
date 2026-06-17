from django.urls import path, include

urlpatterns = [
    path('', include('app.core.urls')),
    path('', include('app.hair.urls')),
    path('', include('app.makeup.urls')),
]
