from django.conf import settings
from rest_framework import serializers
from .models import User, HairStyle, MakeupStyle, AnalysisSession, StyleMappingList, SimulationResult, UserFeedback


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
        fields = '__all__'


class SimulationResultSerializer(serializers.ModelSerializer):
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)

    class Meta:
        model = SimulationResult
        fields = '__all__'
        read_only_fields = ['created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # 마이홈 호환 형식으로 변환
        session = instance.analysis_session
        request = self.context['request']
        data['date'] = instance.created_at.strftime('%Y-%m-%d')
        data['beforeImage'] = request.build_absolute_uri(settings.MEDIA_URL + session.image_path) if session.image_path else ''
        data['afterImage'] = request.build_absolute_uri(settings.MEDIA_URL + instance.generated_image_path) if instance.generated_image_path else ''

        applied_styles = []
        if instance.makeup_mapping:
            applied_styles.append({'type': 'makeup', 'name': instance.makeup_mapping.style_name})
        if instance.hair_mapping:
            applied_styles.append({'type': 'hair', 'name': instance.hair_mapping.style_name})
        data['appliedStyles'] = applied_styles

        return data
