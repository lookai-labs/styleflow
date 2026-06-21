from django.conf import settings
from rest_framework import serializers
from ..models import User, HairStyle, MakeupStyle, AnalysisSession, StyleMappingList, SimulationResult, UserFeedback


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class HairStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = HairStyle
        fields = '__all__'


class MakeupStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MakeupStyle
        fields = '__all__'


class AnalysisSessionSerializer(serializers.ModelSerializer):
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)

    class Meta:
        model = AnalysisSession
        fields = '__all__'
        read_only_fields = ['created_at']


class StyleMappingListSerializer(serializers.ModelSerializer):
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)

    class Meta:
        model = StyleMappingList
        fields = '__all__'
        read_only_fields = ['created_at']


class UserFeedbackSerializer(serializers.ModelSerializer):
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)

    class Meta:
        model = UserFeedback
        fields = ['id', 'user', 'user_nickname', 'simulation_result', 'target_type',
                  'user_chat', 'ai_chat', 'img_url', 'applied_style_key', 'created_at']


class SimulationResultSerializer(serializers.ModelSerializer):
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)

    class Meta:
        model = SimulationResult
        fields = '__all__'
        read_only_fields = ['created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)

        session = instance.analysis_session
        request = self.context['request']
        data['date'] = instance.created_at.strftime('%Y-%m-%d')
        data['beforeImage'] = request.build_absolute_uri(settings.MEDIA_URL + session.image_path) if session.image_path else ''
        data['afterImage'] = request.build_absolute_uri(settings.MEDIA_URL + instance.generated_image_path) if instance.generated_image_path else ''

        applied_styles = []
        makeup_name = (instance.makeup_mapping.style_name if instance.makeup_mapping else None) or instance.makeup_name
        hair_name = (instance.hair_mapping.style_name if instance.hair_mapping else None) or instance.hair_name
        if makeup_name:
            applied_styles.append({'type': 'makeup', 'name': makeup_name})
        if hair_name:
            applied_styles.append({'type': 'hair', 'name': hair_name})
        data['appliedStyles'] = applied_styles

        return data
