from django.contrib import admin
from ..models import (
    User, HairStyle, MakeupStyle,
    AnalysisSession, StyleMappingList, SimulationResult, UserFeedback
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'nickname', 'gender', 'role', 'created_at']
    list_filter = ['gender', 'role']
    search_fields = ['nickname']


@admin.register(HairStyle)
class HairStyleAdmin(admin.ModelAdmin):
    list_display = ['id', 'hair_code', 'style_name', 'image_url']
    search_fields = ['style_name', 'hair_code']


@admin.register(MakeupStyle)
class MakeupStyleAdmin(admin.ModelAdmin):
    list_display = ['id', 'style_name', 'image_url']
    search_fields = ['style_name']


@admin.register(AnalysisSession)
class AnalysisSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'face_shape', 'face_point', 'skin_tone', 'created_at']
    list_filter = ['face_shape', 'skin_tone']
    search_fields = ['user__nickname']


@admin.register(StyleMappingList)
class StyleMappingListAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'analysis_session', 'type', 'style_name', 'created_at']
    list_filter = ['type']
    search_fields = ['style_name', 'user__nickname']


@admin.register(SimulationResult)
class SimulationResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'analysis_session', 'makeup_mapping', 'hair_mapping', 'is_saved', 'created_at']
    list_filter = ['is_saved']
    search_fields = ['user__nickname']


@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'simulation_result', 'target_type', 'created_at']
    list_filter = ['target_type']
    search_fields = ['user__nickname']
