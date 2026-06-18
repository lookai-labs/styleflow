from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, AnalysisSessionViewSet,
    StyleMappingListViewSet, SimulationResultViewSet,
    SavedResultViewSet, health_check, simulate_save,
    register, login_view, token_refresh,
    HairStyleViewSet, MakeupStyleViewSet, admin_dashboard, UserFeedbackViewSet,
    analyze, ai_chat,
)

router = DefaultRouter()
router.register(r'admin/users', UserViewSet, basename='user')
router.register(r'admin/analyses', AnalysisSessionViewSet, basename='analysis')
router.register(r'admin/style-mappings', StyleMappingListViewSet, basename='style-mapping')
router.register(r'admin/simulation-results', SimulationResultViewSet, basename='simulation-result')
router.register(r'saved-results', SavedResultViewSet, basename='saved-result')
router.register(r'admin/hair-styles', HairStyleViewSet, basename='admin-hair-style')
router.register(r'admin/makeup-styles', MakeupStyleViewSet, basename='admin-makeup-style')
router.register(r'admin/feedback', UserFeedbackViewSet, basename='admin-feedback')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', health_check, name='health-check'),
    path('simulate/save/', simulate_save, name='simulate-save'),
    path('auth/register/', register, name='auth-register'),
    path('auth/login/', login_view, name='auth-login'),
    path('auth/refresh/', token_refresh, name='auth-refresh'),
    path('admin/dashboard/', admin_dashboard, name='admin-dashboard'),
    path('analyze/', analyze, name='analyze'),
    path('ai-chat/', ai_chat, name='ai-chat'),
]
