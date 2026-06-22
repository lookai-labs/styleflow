import logging
import os
import sys
import uuid
from pathlib import Path

from django.conf import settings

# face_analysis 경로 등록 (diagnose, Recommend 모듈의 flat import 구조 대응)
_FA_DIR = Path(__file__).parent.parent / 'face_analysis'
if str(_FA_DIR) not in sys.path:
    sys.path.insert(0, str(_FA_DIR))

from django.contrib.auth.hashers import make_password, check_password
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from ..models import User, HairStyle, MakeupStyle, AnalysisSession, StyleMappingList, SimulationResult, UserFeedback

logger = logging.getLogger(__name__)
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

# ChromaDB metadata와 정확히 일치해야 RAG 필터가 동작함
_FACE_PROPORTION_MAP = {
    'upper': '상안부_긴형',
    'middle': '중안부_긴형',
    'lower': '하안부_긴형',
    'golden': '균형',
}

_PERSONAL_COLOR_MAP = {
    'spring': '봄웜',
    'summer': '여름쿨',
    'fall': '가을웜',
    'winter': '겨울쿨',
}

_GENDER_MAP = {
    'female': '여성',
    'male': '남성',
}

_FACE_SHAPE_MAP = {
    'round': '둥근형',
    'oval': '계란형',
    'square': '각진형',
    'heart': '역삼각형',
    'oblong': '장방형',
    'long': '장방형',
}

# style_code, makeup_group 은 추후 MakeupStyle 모델 필드로 교체 예정
_MAKEUP_DUMMY_META = {
    '웜 코랄 메이크업': {'style_code': 'MS1', 'makeup_group': 'coral'},
    '소프트 뉴트럴':    {'style_code': 'MS2', 'makeup_group': 'neutral'},
    '로즈 글로우':      {'style_code': 'MS3', 'makeup_group': 'rose'},
}

_CHATBOT_DUMMY_RECOMMENDATIONS = [
    {'category': 'hair',   'style_name': '퀴프',          'style_code': 'm-10'},
    {'category': 'makeup', 'style_name': '코랄 메이크업', 'style_code': 'mk-sp-coral', 'makeup_group': 'spring_coral'},
]

_DUMMY_HAIR_STYLES = [
    {'style_name': '퀴프',       'style_code': 'm-10'},
    {'style_name': '포마드',     'style_code': 'm-16'},
    {'style_name': '아이비리그', 'style_code': 'm-03'},
]

_DUMMY_MAKEUP_STYLES = [
    {'style_name': '코랄 메이크업',      'style_code': 'mk-sp-coral',    'makeup_group': 'spring_coral'},
    {'style_name': '피치 메이크업',      'style_code': 'mk-sp-peach',    'makeup_group': 'spring_peach'},
    {'style_name': '봄웜 내추럴 메이크업', 'style_code': 'mk-m-sp-natural', 'makeup_group': 'male_spring_natural'},
]

# 추천 로직 미구현 구간 더미 데이터
_DUMMY_HAIR_RECOMMENDATIONS = [
    {'style_name': '아이비리그', 'style_code': 'm-03'},
    {'style_name': '댄디',      'style_code': 'm-08'},
    {'style_name': '애즈',      'style_code': 'm-12'},
]

_DUMMY_MAKEUP_MALE = [
    {'style_name': '봄웜 내추럴 메이크업', 'style_code': 'mk-m-sp-natural', 'makeup_group': 'male_spring_natural'},
]


def _samjeong_to_face_point(samjeong: dict | None) -> str:
    if not samjeong or samjeong.get('is_balanced', True):
        return 'golden'
    longest = samjeong.get('longest', '')
    if '상안부' in longest:
        return 'upper'
    if '중안부' in longest:
        return 'middle'
    if '하안부' in longest:
        return 'lower'
    return 'golden'


def _personal_color_to_skin_tone(pc: dict | None) -> str | None:
    if not pc or pc.get('error'):
        return None
    label = pc.get('final_label')
    if not label:
        label = (pc.get('top1') or {}).get('label', '')
    return {
        'spring_warm':  'spring',
        'summer_cool':  'summer',
        'autumn_warm':  'fall',
        'winter_cool':  'winter',
    }.get(label)


@api_view(['POST'])
@parser_classes([MultiPartParser])
def analyze(request):
    """
    얼굴 사진 → AI 분석(face_analysis) → RAG 추천 요약 → DB 저장 → 결과 반환.
    """
    gender = getattr(request.user, 'gender', 'female')
    rag_gender = _GENDER_MAP.get(gender, '여성')

    # ① 이미지 저장
    face_image = request.FILES.get('face_image')
    if not face_image:
        return Response({'error': '얼굴 이미지가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    save_dir = os.path.join(settings.MEDIA_ROOT, 'analyses')
    os.makedirs(save_dir, exist_ok=True)
    ext = os.path.splitext(face_image.name)[1] or '.jpg'
    filename = f"{uuid.uuid4().hex}{ext}"
    abs_image_path = os.path.join(save_dir, filename)
    with open(abs_image_path, 'wb') as f:
        for chunk in face_image.chunks():
            f.write(chunk)
    image_path = f'analyses/{filename}'

    # ② AI 분석 (얼굴형 + 삼정 + 퍼스널컬러)
    try:
        from diagnose import diagnose as fa_diagnose
        from Recommend import recommend as fa_recommend
        diagnosis = fa_diagnose(abs_image_path)
        recommendation = fa_recommend(diagnosis, gender)
    except Exception as e:
        logger.error("Face_Analysis 실패: user_id=%s, error=%s", request.user.id, e, exc_info=True)
        return Response({'error': 'AI 분석 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ③ 분석 결과 → DB 필드 매핑
    fs = diagnosis.get('face_shape') or {}
    sj = diagnosis.get('samjeong')
    pc = diagnosis.get('personal_color') or {}

    face_shape_en   = fs.get('label_en', 'round')
    face_point      = _samjeong_to_face_point(sj)
    skin_tone       = _personal_color_to_skin_tone(pc)

    rag_face_shape   = _FACE_SHAPE_MAP.get(face_shape_en, face_shape_en)
    face_proportion  = _FACE_PROPORTION_MAP.get(face_point, '균형')
    personal_color_ko = pc.get('display_name') or _PERSONAL_COLOR_MAP.get(skin_tone, '봄웜')

    sj_ratios = (sj or {}).get('ratios', {})

    # ④ AnalysisSession 생성
    session = AnalysisSession.objects.create(
        user_id=request.user.id,
        image_path=image_path,
        face_shape=face_shape_en,
        face_point=face_point,
        skin_tone=skin_tone,
        ratio_upper_third=sj_ratios.get('상안부'),
        ratio_middle_third=sj_ratios.get('중안부'),
        ratio_lower_third=sj_ratios.get('하안부'),
    )

    # ⑤ 추천 스타일 목록 (상위 3개) + RAG용 style_code 미리 조회
    hair_names   = (recommendation.get('hairstyle') or {}).get('recommended', [])[:3]
    makeup_names = (recommendation.get('makeup') or {}).get('recommended', [])[:3]

    hair_code_prefix = 'm-' if gender == 'male' else 'f-'
    recommended_hair_styles = []
    for n in hair_names:
        obj = HairStyle.objects.filter(style_name=n, hair_code__startswith=hair_code_prefix).first()
        recommended_hair_styles.append({'style_name': n, 'style_code': obj.hair_code if obj else ''})

    recommended_makeup_styles = [{'style_name': n} for n in makeup_names]

    # ⑥ RAG 호출
    try:
        from backend.app.rag.analysis_rag.service import generate_analysis_result
        result = generate_analysis_result(
            gender=rag_gender,
            face_shape=rag_face_shape,
            face_proportion=face_proportion,
            recommended_hair_styles=recommended_hair_styles,
            personal_color=personal_color_ko,
            recommended_makeup_styles=recommended_makeup_styles or None,
        )
    except Exception as e:
        logger.error("RAG 분석 실패: user_id=%s, error=%s", request.user.id, e, exc_info=True)
        return Response({'error': 'RAG 분석 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ⑦ StyleMappingList 저장
    hair_mappings = []
    for style in recommended_hair_styles:
        style_name = style['style_name']
        hair_style_obj = HairStyle.objects.filter(style_name=style_name, hair_code__startswith=hair_code_prefix).first()
        style_code = (hair_style_obj.hair_code or '') if hair_style_obj else ''
        mapping = StyleMappingList.objects.create(
            user_id=request.user.id,
            analysis_session=session,
            type='hair',
            hair_style=hair_style_obj,
            style_name=style_name,
        )
        hair_mappings.append({
            'id': mapping.id,
            'style_name': style_name,
            'style_code': style_code,
            'image_url': (hair_style_obj.image_url or '') if hair_style_obj else '',
        })

    makeup_mappings = []
    for style in recommended_makeup_styles:
        style_name = style['style_name']
        if gender == 'male':
            makeup_style_objs = list(MakeupStyle.objects.filter(style_name=style_name))
        else:
            obj = MakeupStyle.objects.filter(style_name=style_name).first()
            makeup_style_objs = [obj] if obj else []
        for makeup_style_obj in makeup_style_objs:
            style_code = (makeup_style_obj.style_code or '') if makeup_style_obj else ''
            mapping = StyleMappingList.objects.create(
                user_id=request.user.id,
                analysis_session=session,
                type='makeup',
                makeup_style=makeup_style_obj,
                style_name=style_name,
            )
            makeup_mappings.append({
                'id': mapping.id,
                'style_name': style_name,
                'style_code': style_code,
                'image_url': (makeup_style_obj.image_url or '') if makeup_style_obj else '',
            })

    return Response({
        'hair_analysis_summary':   result['hair_analysis_summary'],
        'makeup_analysis_summary': result.get('makeup_analysis_summary'),
        'face_shape':              rag_face_shape,
        'skin_tone':               skin_tone,
        'personal_color':          personal_color_ko,
        'analysis_session_id':     session.id,
        'hair_mappings':           hair_mappings,
        'makeup_mappings':         makeup_mappings,
    })


@api_view(['POST'])
def ai_chat(request):
    """
    챗봇 상담 답변 생성.

    run_chatbot() LangGraph 그래프로 의도 분류, RAG 검색, 답변 생성을 수행한다.
    previous_recommendations는 실제 추천 모듈 연결 전까지 더미 데이터를 사용한다.
    """
    message = request.data.get('message', '').strip()
    if not message:
        return Response({'error': '메시지를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    face_shape = request.data.get('face_shape', '둥근형')
    personal_color = request.data.get('personal_color', '봄웜')
    gender_raw = getattr(request.user, 'gender', 'female')
    gender = _GENDER_MAP.get(gender_raw, '여성')
    face_proportion = _FACE_PROPORTION_MAP.get('golden', '균형')
    sim_image_url = request.data.get('sim_image_url') or None

    previous_analysis = request.data.get('previous_analysis') or (
        "둥근형 얼굴에 어울리는 레이어드 웨이브 헤어스타일과 봄 웜톤에 맞는 코랄 메이크업을 추천드립니다."
    )

    # DB에서 이전 대화 이력 로드 (created_at 오름차순 → 과거→최신)
    from backend.app.rag.chatbot_rag.memory import db_rows_to_chat_history, MAX_CHAT_HISTORY_TURNS
    db_rows = list(
        UserFeedback.objects
        .filter(user_id=request.user.id)
        .exclude(user_chat__isnull=True)
        .order_by('-created_at')
        .values('user_chat', 'ai_chat')[:MAX_CHAT_HISTORY_TURNS]
    )[::-1]  # 역순 → 오름차순 복원
    chat_history = db_rows_to_chat_history(db_rows) or (request.data.get('chat_history') or [])

    user_profile = request.data.get('user_profile') or {}
    selected_option = request.data.get('selected_option') or None
    previous_recommendations = request.data.get('previous_recommendations') or _CHATBOT_DUMMY_RECOMMENDATIONS

    raw_target_type = request.data.get('target_type') or None
    target_type = raw_target_type if raw_target_type in {'hair', 'makeup'} else None
    applied_style_key = request.data.get('applied_style_key') or None
    logger.info(
        "[ai_chat] user_id=%s message=%r target_type=%s applied_style_key=%s",
        request.user.id, message, target_type, applied_style_key,
    )

    try:
        from backend.app.rag.chatbot_rag.graph import run_chatbot
        result = run_chatbot(
            user_message=message,
            gender=gender,
            face_shape=face_shape,
            face_proportion=face_proportion,
            personal_color=personal_color,
            previous_analysis=previous_analysis,
            previous_recommendations=previous_recommendations,
            chat_history=chat_history,
            user_profile=user_profile,
            selected_option=selected_option,
            sim_image_url=sim_image_url,
            target_type=target_type,
            applied_style_key=applied_style_key,
        )
    except Exception as e:
        logger.error("챗봇 답변 생성 실패: user_id=%s, error=%s", request.user.id, e, exc_info=True)
        return Response({'error': '챗봇 답변 생성 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    retouched_image_url = result.get('retouched_image_url')
    if retouched_image_url and retouched_image_url.startswith('/'):
        retouched_image_url = request.build_absolute_uri(retouched_image_url)

    outfit_result_image_url = result.get('outfit_result_image_url')
    if outfit_result_image_url and outfit_result_image_url.startswith('/'):
        outfit_result_image_url = request.build_absolute_uri(outfit_result_image_url)

    return Response({
        'reply': result.get('answer', ''),
        'updated_chat_history': result.get('updated_chat_history', []),
        'updated_user_profile': result.get('updated_user_profile', {}),
        'selection': result.get('selection'),
        'pending_selection': result.get('pending_selection'),
        'retouched_image_url': retouched_image_url,
        'outfit_result_image_url': outfit_result_image_url,
        'category': result.get('category'),
    })


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

    is_saved = str(request.data.get('is_saved', 'false')).lower() not in ('false', '0', '')

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
        is_saved=is_saved,
        generated_image_path=after_image_filename,
        makeup_name=request.data.get('makeup_name', ''),
        hair_name=request.data.get('hair_name', ''),
    )
    sim.save()

    serializer = SimulationResultSerializer(sim, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
def simulate_save_mark(request, pk):
    """기존 SimulationResult를 마이홈 저장 상태(is_saved=True)로 업데이트."""
    try:
        sim = SimulationResult.objects.get(id=pk, user_id=request.user.id)
    except SimulationResult.DoesNotExist:
        return Response({'error': '결과를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    sim.is_saved = True
    sim.save()
    serializer = SimulationResultSerializer(sim, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
def feedback_chat(request):
    """채팅 한 쌍(user_chat + ai_chat)을 user_feedback에 저장."""
    user_chat = request.data.get('user_chat', '')
    ai_chat = request.data.get('ai_chat', '')
    target_type = request.data.get('target_type', 'makeup')
    simulation_result_id = request.data.get('simulation_result_id')
    applied_style_key = request.data.get('applied_style_key') or ''
    img_url = request.data.get('img_url') or None

    sim_result = None
    if simulation_result_id:
        try:
            sim_result = SimulationResult.objects.get(id=simulation_result_id)
        except SimulationResult.DoesNotExist:
            pass

    UserFeedback.objects.create(
        user_id=request.user.id,
        simulation_result=sim_result,
        target_type=target_type if target_type in ('hair', 'makeup') else 'makeup',
        user_chat=user_chat,
        ai_chat=ai_chat,
        applied_style_key=applied_style_key,
        img_url=img_url,
    )

    return Response({'ok': True}, status=status.HTTP_201_CREATED)
