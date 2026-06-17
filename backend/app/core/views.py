import os
import uuid

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from ..models import User, HairStyle, MakeupStyle, AnalysisSession, StyleMappingList, SimulationResult, UserFeedback
from .serializers import (
    UserSerializer, HairStyleSerializer, MakeupStyleSerializer,
    AnalysisSessionSerializer, StyleMappingListSerializer, SimulationResultSerializer,
    UserFeedbackSerializer,
)


# ── 인증 뷰 ──────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    nickname = request.data.get('nickname', '').strip()
    password = request.data.get('password', '')
    gender = request.data.get('gender', '')

    if not nickname or not password or not gender:
        return Response({'error': '모든 필드를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(nickname=nickname).exists():
        return Response({'error': '이미 사용 중인 닉네임입니다.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create(
        nickname=nickname,
        password=make_password(password),
        gender=gender,
        role='user',
    )

    refresh = RefreshToken()
    refresh['user_id'] = user.id
    refresh['nickname'] = user.nickname
    refresh['role'] = user.role

    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {'id': user.id, 'nickname': user.nickname, 'role': user.role},
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    nickname = request.data.get('nickname', '').strip()
    password = request.data.get('password', '')

    if not nickname or not password:
        return Response({'error': '아이디와 비밀번호를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(nickname=nickname)
    except User.DoesNotExist:
        return Response({'error': '존재하지 않는 아이디입니다.'}, status=status.HTTP_400_BAD_REQUEST)

    if not check_password(password, user.password):
        return Response({'error': '비밀번호가 틀렸습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    refresh = RefreshToken()
    refresh['user_id'] = user.id
    refresh['nickname'] = user.nickname
    refresh['role'] = user.role

    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {'id': user.id, 'nickname': user.nickname, 'role': user.role},
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def token_refresh(request):
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({'error': 'refresh token이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        refresh = RefreshToken(refresh_token)
        return Response({'access': str(refresh.access_token)})
    except TokenError:
        return Response({'error': '유효하지 않은 refresh token입니다.'}, status=status.HTTP_401_UNAUTHORIZED)


# ── 권한 클래스 ──────────────────────────────────────────────────────────

class IsAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'admin'


# ── 관리자 전용 뷰셋 ─────────────────────────────────────────────────────

class HairStyleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    queryset = HairStyle.objects.all().order_by('id')
    serializer_class = HairStyleSerializer


class MakeupStyleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    queryset = MakeupStyle.objects.all().order_by('id')
    serializer_class = MakeupStyleSerializer


@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_dashboard(request):
    from django.db.models import Count

    skin_tone_dist = (
        AnalysisSession.objects
        .exclude(skin_tone__isnull=True)
        .values('skin_tone')
        .annotate(count=Count('skin_tone'))
        .order_by('skin_tone')
    )
    face_shape_dist = (
        AnalysisSession.objects
        .exclude(face_shape__isnull=True)
        .values('face_shape')
        .annotate(count=Count('face_shape'))
        .order_by('face_shape')
    )

    return Response({
        'total_users': User.objects.count(),
        'total_sessions': AnalysisSession.objects.count(),
        'skin_tone_distribution': list(skin_tone_dist),
        'face_shape_distribution': list(face_shape_dist),
    })


# ── 일반 뷰셋 (관리자 전용) ───────────────────────────────────────────────

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class AnalysisSessionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    serializer_class = AnalysisSessionSerializer

    def get_queryset(self):
        from django.db.models import Q
        qs = AnalysisSession.objects.select_related('user').all()
        user_id = self.request.query_params.get('user_id')
        if user_id:
            qs = qs.filter(user_id=user_id)
        if self.request.query_params.get('anomaly') == 'true':
            qs = qs.filter(
                Q(face_shape__isnull=True) |
                Q(skin_tone__isnull=True) |
                Q(face_point__isnull=True)
            )
        return qs


class UserFeedbackViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdmin]
    serializer_class = UserFeedbackSerializer

    def get_queryset(self):
        qs = UserFeedback.objects.select_related('user').order_by('-created_at')
        target_type = self.request.query_params.get('target_type')
        if target_type:
            qs = qs.filter(target_type=target_type)
        return qs


class StyleMappingListViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    queryset = StyleMappingList.objects.all()
    serializer_class = StyleMappingListSerializer


class SimulationResultViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    queryset = SimulationResult.objects.all()
    serializer_class = SimulationResultSerializer


class SavedResultViewSet(viewsets.ModelViewSet):
    serializer_class = SimulationResultSerializer
    http_method_names = ['get', 'delete']

    def get_queryset(self):
        return SimulationResult.objects.filter(
            is_saved=True,
            user_id=self.request.user.id,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_saved = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── 기능 뷰 ──────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({'status': 'ok', 'service': 'StyleFlow API'})


@api_view(['POST'])
@parser_classes([MultiPartParser])
def simulate_save(request):
    face_image = request.FILES.get('face_image')
    after_image_filename = request.data.get('after_image_filename', '')

    if not face_image or not after_image_filename:
        return Response(
            {'error': 'face_image와 after_image_filename이 필요합니다.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    save_dir = os.path.join(settings.MEDIA_ROOT, 'analyses')
    os.makedirs(save_dir, exist_ok=True)
    ext = os.path.splitext(face_image.name)[1] or '.png'
    filename = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(save_dir, filename), 'wb') as f:
        for chunk in face_image.chunks():
            f.write(chunk)

    session = AnalysisSession.objects.create(
        user_id=request.user.id,
        image_path=f'analyses/{filename}',
    )

    sim = SimulationResult(
        user_id=request.user.id,
        analysis_session=session,
        is_saved=True,
        generated_image_path=f'simulations/{after_image_filename}',
    )
    sim.save()

    serializer = SimulationResultSerializer(sim, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)
