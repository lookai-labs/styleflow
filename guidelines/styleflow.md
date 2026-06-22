# StyleFlow — 프로젝트 문서

> **Next.js 15 (App Router + Tailwind CSS)** + **Django 5.2 (DRF + MariaDB)** 풀스택 아키텍처

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 서비스명 | StyleFlow |
| 설명 | AI 기반 얼굴형·피부톤·스타일 분석 및 시뮬레이션 서비스 |
| 프론트엔드 | Next.js 15 (App Router) + Tailwind CSS + shadcn/ui |
| 백엔드 | Django 5.2 + DRF + djangorestframework-simplejwt |
| DB | MariaDB (원격: 220.80.16.79:3306, DB: styleflowdb) |
| 인증 | JWT (access 1시간, refresh 7일) |

---

## 2. 폴더 구조

```
pj_styleflow/
├── frontend/                   ← Next.js 15 (App Router)
│   ├── app/
│   │   ├── layout.tsx          ← AuthProvider 감싸기
│   │   ├── page.tsx            ← 랜딩 페이지
│   │   ├── not-found.tsx
│   │   ├── login/page.tsx
│   │   ├── signup/page.tsx
│   │   ├── upload/page.tsx
│   │   ├── result/[type]/page.tsx
│   │   ├── ai-stylist/page.tsx
│   │   ├── simulation/page.tsx
│   │   ├── simulation-flow/page.tsx
│   │   ├── simulation-complete/page.tsx
│   │   ├── my-home/page.tsx
│   │   └── admin/
│   │       ├── layout.tsx      ← 관리자 사이드바 레이아웃
│   │       ├── page.tsx        ← 대시보드
│   │       ├── styles/page.tsx ← 스타일 CRUD
│   │       ├── users/page.tsx  ← 사용자 관리
│   │       ├── feedback/page.tsx
│   │       ├── sessions/page.tsx   ← 세션 이상 데이터 검수
│   │       ├── simulations/page.tsx
│   │       └── mappings/page.tsx   ← 추천 결과 검수
│   ├── components/
│   │   ├── Header.tsx          ← role='admin'이면 관리자 헤더 렌더
│   │   ├── Footer.tsx
│   │   ├── StylingSelectionModal.tsx
│   │   └── ui/                 ← shadcn/ui 컴포넌트
│   ├── context/
│   │   └── AuthContext.tsx     ← 전역 인증 상태 (user, isLoggedIn, login, logout)
│   ├── hooks/
│   │   ├── useRequireAuth.ts   ← 비로그인 시 /login 리다이렉트
│   │   └── useRequireAdmin.ts  ← 비관리자 시 / 리다이렉트
│   ├── lib/
│   │   ├── api.ts              ← axios 인스턴스 + 토큰 자동 첨부 + 401 갱신
│   │   ├── auth.ts             ← localStorage 토큰 저장/조회
│   │   └── utils.ts
│   └── public/
│       ├── reference/
│       │   └── makeup/         ← BeautyGAN 폴백용 레퍼런스 이미지 (MS1~3.png)
│       └── images/
│           ├── hair/           ← 헤어스타일 썸네일 (hair_styles.image_url 경로)
│           └── makeup/         ← 메이크업 썸네일 (makeup_styles.image_url 경로)
│               └── temp/       ← 남성 메이크업 임시 이미지 (male-{season}-{n}.png)
│
└── backend/                    ← Django 5.2 + DRF
    ├── app/                    ← 메인 Django 앱
    │   ├── models.py           ← 7개 테이블
    │   ├── migrations/
    │   ├── urls.py             ← core/hair/makeup include
    │   ├── apps.py
    │   ├── core/               ← 인증, 공통 뷰셋, 시리얼라이저
    │   │   ├── views.py        ← 인증, 관리자, ViewSet, simulate_save
    │   │   ├── urls.py
    │   │   ├── serializers.py
    │   │   ├── authentication.py ← CustomJWTAuthentication
    │   │   └── admin.py
    │   ├── hair/               ← HairFastGAN
    │   │   ├── views.py        ← simulate_hair
    │   │   ├── urls.py
    │   │   └── services.py
    │   ├── makeup/             ← BeautyGAN
    │   │   ├── views.py        ← simulate_makeup
    │   │   ├── urls.py
    │   │   └── services.py
    │   └── rag/                ← RAG 모듈
    │       ├── analysis_rag/   ← 분석 결과 요약 (generate_analysis_result)
    │       ├── chatbot_rag/    ← LangGraph 챗봇 (run_chatbot, retouch)
    │       ├── crawler/        ← 데이터 수집
    │       ├── rag_core/       ← ChromaDB 검색/생성 공통 유틸
    │       └── vector_index/   ← 임베딩 및 벡터 인덱스 빌드
    ├── app/
    │   └── face_analysis/      ← Face_Analysis 패키지 (diagnose, Recommend)
    │       ├── diagnose.py     ← 얼굴형 + 삼정 + 퍼스널컬러 통합 진단
    │       ├── Recommend.py    ← 성별 기반 헤어/메이크업 추천 (hair.md, makeup.xlsx)
    │       ├── shape/          ← 얼굴형 분류 모델
    │       └── skin/           ← 퍼스널컬러 모델 번들
    ├── gan_models/
    │   ├── HairFastGAN-p310/
    │   │   └── imgs/hair/      ← 폴백용 레퍼런스 이미지 (MH1~3.jpg)
    │   └── BeautyGAN-master-p310/
    │       └── imgs/makeup/    ← 폴백용 레퍼런스 이미지 (MS1~3.png)
    ├── media/                  ← 런타임 생성 (MEDIA_ROOT, git 제외)
    │   ├── analyses/           ← 사용자가 업로드한 원본 사진
    │   └── simulations/        ← GAN 결과 이미지
    ├── styleflow/
    │   ├── settings.py
    │   └── urls.py
    ├── vector_data/            ← ChromaDB 벡터 인덱스 (git 제외)
    │   └── chroma/
    ├── manage.py
    ├── run.bat
    ├── .env
    └── .env.example

requirements.txt               ← 루트(pj_styleflow/)에 위치 (backend/ 아님)
```

---

## 3. 라우트 목록

| URL | 파일 | 인증 |
|-----|------|------|
| `/` | `app/page.tsx` | 누구나 |
| `/login` | `app/login/page.tsx` | 누구나 |
| `/signup` | `app/signup/page.tsx` | 누구나 |
| `/upload` | `app/upload/page.tsx` | 로그인 필요 |
| `/result/:type` | `app/result/[type]/page.tsx` | 로그인 필요 |
| `/simulation-flow` | `app/simulation-flow/page.tsx` | 로그인 필요 |
| `/simulation-complete` | `app/simulation-complete/page.tsx` | 로그인 필요 |
| `/my-home` | `app/my-home/page.tsx` | 로그인 필요 |
| `/admin/*` | `app/admin/` | 관리자 전용 |

---

## 4. 인증 흐름 (JWT)

```
회원가입/로그인 (POST /api/auth/register/ or /login/)
    ↓
서버: access token + refresh token + user 정보 반환
    ↓
프론트: localStorage 저장 (sf_access, sf_refresh, sf_user)
        AuthContext의 user 상태 업데이트
    ↓
이후 모든 API 요청: lib/api.ts interceptor가 Authorization: Bearer {token} 자동 첨부
    ↓
401 응답 시: refresh token으로 access token 갱신 후 원 요청 재시도
            갱신 실패 시: localStorage 초기화 + /login 리다이렉트
```

**토큰 관련 설정 (settings.py)**
```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "USER_ID_CLAIM": "user_id",
}
```

**커스텀 인증 클래스 (api/authentication.py)**
- 기본 simplejwt는 Django AbstractBaseUser 기반 → 커스텀 User 모델과 호환 안 됨
- `CustomJWTAuthentication.get_user()` 오버라이드로 `api.models.User` 직접 조회

---

## 5. 백엔드 API 명세

**Base URL:** `http://localhost:8000/api/`

### 인증

| Method | URL | 권한 | 설명 |
|--------|-----|------|------|
| POST | `/auth/register/` | 누구나 | 회원가입, JWT 반환 |
| POST | `/auth/login/` | 누구나 | 로그인, JWT 반환 |
| POST | `/auth/refresh/` | 누구나 | access token 갱신 |

### 일반 사용자

| Method | URL | 설명 |
|--------|-----|------|
| POST | `/analyze/` | 얼굴 분석 → 스타일 추천 → DB 저장 → 결과 반환 |
| POST | `/simulate/makeup/` | BeautyGAN 메이크업 시뮬레이션 |
| POST | `/simulate/hair/` | HairFastGAN 헤어 시뮬레이션 |
| POST | `/simulate/save/` | 시뮬레이션 결과 저장 (is_saved=false로 자동 생성) |
| PATCH | `/simulate/save/{id}/` | 저장 확정 (is_saved=true) |
| GET | `/saved-results/` | 내 저장 결과 목록 |
| DELETE | `/saved-results/{id}/` | 저장 결과 삭제 (is_saved=false) |
| GET | `/health/` | 서버 상태 확인 |

### 관리자 전용 (role='admin' 필요)

| Method | URL | 설명 |
|--------|-----|------|
| GET/POST | `/admin/hair-styles/` | 헤어스타일 목록/추가 |
| GET/PUT/DELETE | `/admin/hair-styles/{id}/` | 헤어스타일 수정/삭제 |
| GET/POST | `/admin/makeup-styles/` | 메이크업스타일 목록/추가 |
| GET/PUT/DELETE | `/admin/makeup-styles/{id}/` | 메이크업스타일 수정/삭제 |
| GET | `/admin/dashboard/` | 통계 (사용자 수, 세션 수, 분포) |
| GET | `/admin/feedback/` | 피드백 목록 (`?target_type=hair\|makeup`) |
| GET | `/admin/users/` | 전체 사용자 목록 |
| GET | `/admin/analyses/` | 분석 세션 목록 (`?user_id=`, `?anomaly=true`) |
| GET | `/admin/simulation-results/` | 시뮬레이션 결과 목록 |
| DELETE | `/admin/simulation-results/{id}/` | 결과 삭제 |
| GET | `/admin/style-mappings/` | 추천 결과 목록 |

> **페이지네이션**: 모든 목록 API는 `{ count, next, previous, results: [...] }` 형태로 반환 (PAGE_SIZE=20)

---

## 6. Django 데이터베이스 모델 (7개 테이블)

```python
class User                # users — nickname, password, gender, role, created_at
class HairStyle           # hair_styles — hair_code(m-/f- 접두어), style_name, image_url
class MakeupStyle         # makeup_styles — style_code(null, unique 없음), style_name, image_url
                          #   ※ 남성 메이크업: 동일 style_code로 3행 (이미지 3장)
                          #   ※ 여성 메이크업: 12개 스타일, 남성: 4개 시즌 × 3행 = 12행
class AnalysisSession     # analysis_sessions — user_id, image_path, face_shape, face_point,
                          #   skin_tone, skin_lab_b, ratio_*, result(JSON), created_at
class StyleMappingList    # style_mapping_list — user_id, analysis_session_id, type,
                          #   hair_style_id, makeup_style_id, style_name, created_at
class SimulationResult    # simulation_results — user_id, analysis_session_id,
                          #   hair_mapping_id, makeup_mapping_id,
                          #   generated_image_path, is_saved,
                          #   makeup_name, hair_name, created_at
class UserFeedback        # user_feedback — user_id, simulation_result_id,
                          #   target_type, user_chat, ai_chat, applied_style_key, img_url, created_at
```

**주의:** `User`는 `models.Model`만 상속 (AbstractBaseUser 미사용)  
DRF `IsAuthenticated` 호환을 위해 `is_authenticated = property(lambda self: True)` 직접 추가

---

## 6-1. GAN 시뮬레이션 (메이크업 + 헤어)

### BeautyGAN 메이크업

TensorFlow 2.13 기반. 원본 사진에 메이크업 전이.

**처리 흐름:**
```
원본 이미지
    ↓ dlib — 얼굴 감지 + 5점 랜드마크 → 256×256 chip 추출
    ↓ BeautyGAN TF 세션 — 레퍼런스 메이크업 이미지와 쌍으로 추론
    ↓ mediapipe FaceMesh — 원본 해상도 얼굴 마스크 생성
    ↓ Affine 역변환 + Feathered 블렌딩 → 원본 해상도 결과 이미지
```

### HairFastGAN 헤어

PyTorch 기반. 레퍼런스 헤어스타일 이미지를 원본 얼굴에 합성.

### 동적 레퍼런스 이미지

분석 추천 결과(`hair_mappings`/`makeup_mappings`)의 `image_url`을 GAN 레퍼런스로 사용.

```
프론트엔드: localStorage에서 analysis_result 직접 파싱
    → reference_images JSON을 formData에 포함해 API 전송

백엔드 services.py: _resolve_reference_images()
    → URL(/images/...) → frontend/public/ 로컬 경로 매핑
    → 파일 없거나 image_url 없으면 REFERENCE_IMAGES(MH1~3/MS1~3) 폴백
```

**주의:** localStorage 상태 대신 직접 파싱해야 함 — useEffect 타이밍 race condition으로 상태가 null일 수 있음.

---

## 7. 환경 설정

### 프론트엔드 주요 의존성
```json
{
  "next": "^15.x",
  "react": "^18.x",
  "tailwindcss": "^4.x",
  "axios": "latest",
  "@radix-ui/react-dialog": "latest",
  "@radix-ui/react-tabs": "latest"
}
```

### 백엔드 환경 (`p310_pj_styleflow` — Python 3.10)

> 전체 목록은 루트 `requirements.txt` 참조. 아래는 주요 패키지.

```
# 이미지/AI
numpy==1.26.4
opencv-contrib-python==4.8.1.78
Pillow==10.0.0
mediapipe==0.10.9          ← Solutions API (FaceMesh) 사용, Tasks API 아님
tensorflow-intel==2.13.0   ← conda 별도 설치
dlib==19.24.1              ← conda-forge 별도 설치

# 머신러닝
scikit-learn==1.7.2        ← 1.2.2→1.7.2 업그레이드 (Face_Analysis 모델 호환)
lightgbm==4.6.0            ← Face_Analysis 얼굴형/퍼스널컬러 분류
openpyxl==3.1.5            ← Face_Analysis makeup.xlsx 파싱
scipy==1.10.1

# Django
Django==5.2.14
djangorestframework==3.17.1
django-cors-headers==4.9.0
djangorestframework-simplejwt==5.4.0
python-dotenv==1.2.2
mysqlclient==2.2.8

# RAG
chromadb==1.5.9
langchain-chroma==1.1.0
langchain-google-genai==4.2.5
langgraph==1.2.5
sentence-transformers==3.0.1
transformers==4.44.2
protobuf==6.33.6           ← chromadb 기준, mediapipe와 충돌 → monkey patch로 해결

# GAN
torch==1.13.1              ← 별도 설치 (CPU: whl/cpu, GPU: cu117)
torchvision==0.14.1        ← 별도 설치
clip==1.0                  ← git 소스 별도 설치
```

### 환경변수 (`backend/.env`)

```env
SECRET_KEY=django-insecure-...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.mysql
DB_NAME=styleflowdb
DB_USER=styleflow
DB_PASSWORD=0915
DB_HOST=220.80.16.79
DB_PORT=3306

CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## 8. 서버 실행 방법

### 프론트엔드

```bash
cd frontend
npm install       # 최초 1회
npm run dev       # → http://localhost:3000
```

### 백엔드

```bash
# 통합 conda 환경 활성화 필수
conda activate p310_pj_styleflow

cd backend
pip install -r requirements.txt   # 최초 1회

# 마이그레이션
python manage.py makemigrations
python manage.py migrate
# 원격 DB에 테이블이 미리 존재하는 경우:
# python manage.py migrate --fake-initial

# 개발 서버 (--noreload 필수 — TF 세션 중복 로드 방지)
python manage.py runserver --noreload
# → http://localhost:8000
```

### 관리자 계정 (DB에 생성됨)
| 항목 | 값 |
|------|-----|
| nickname | admin |
| password | 1234 |
| role | admin |

---

## 9. 프론트엔드 ↔ 백엔드 데이터 흐름

```
회원가입/로그인
    [login/page.tsx or signup/page.tsx]
    POST /api/auth/login/ or /register/
        → access, refresh, user 반환
        → AuthContext.login() 호출 → localStorage 저장 + Context 상태 업데이트
        → role='admin'이면 /admin, 일반 사용자면 / 로 이동

얼굴 분석
    [upload/page.tsx]
    POST /api/analyze/ (multipart: face_image)
        → Face_Analysis: diagnose() → 얼굴형 + 삼정 + 퍼스널컬러
        → Recommend: recommend(diagnosis, gender) → 헤어/메이크업 스타일명 목록
        → HairStyle DB 조회 (style_name + hair_code prefix로 gender 필터)
        → RAG: generate_analysis_result() → 분석 요약 텍스트
        → AnalysisSession 생성 (face_shape, face_point, skin_tone, 삼정 비율)
        → StyleMappingList 생성 (헤어 3개 + 메이크업 3개)
        → 응답: { hair_analysis_summary, makeup_analysis_summary, face_shape,
                  skin_tone, personal_color, analysis_session_id,
                  hair_mappings: [{id, style_name, style_code, image_url}],
                  makeup_mappings: [{id, style_name, style_code, image_url}] }
        → localStorage: styleflow_analysis_result 저장
        → [result/face/page.tsx]

사진 업로드 + 시뮬레이션
    [result/face/page.tsx] → 시뮬레이션 시작 버튼 → StylingSelectionModal
        → [simulation-flow/page.tsx]

    ── 케이스 1: 메이크업만 ──
    POST /api/simulate/makeup/ (multipart)
        → BeautyGAN 처리 → 결과 이미지 3장 URL 반환
        → 사용자가 1장 선택
        → 확정  OR  [ai-stylist/page.tsx] AI 채팅으로 생성형 이미지 수정
        → 선택/수정된 이미지 URL → localStorage 저장
        → [simulation-complete/page.tsx]

    ── 케이스 2: 헤어만 ──
    POST /api/simulate/hair/ (multipart)
        → HairFastGAN 처리 → 결과 이미지 3장 URL 반환
        → 사용자가 1장 선택
        → 확정  OR  [ai-stylist/page.tsx] AI 채팅으로 생성형 이미지 수정
        → 선택/수정된 이미지 URL → localStorage 저장
        → [simulation-complete/page.tsx]

    ── 케이스 3: 메이크업 + 헤어 ──
    POST /api/simulate/makeup/ (multipart)
        → BeautyGAN 처리 → 결과 이미지 3장 URL 반환
        → 사용자가 1장 선택
        → 확정  OR  [ai-stylist/page.tsx] AI 채팅으로 생성형 이미지 수정
        → 선택/수정된 이미지 URL → localStorage 저장
        ↓
    POST /api/simulate/hair/ (선택된 메이크업 결과 이미지를 입력으로)
        → HairFastGAN 처리 → 결과 이미지 3장 URL 반환
        → 사용자가 1장 선택
        → 확정  OR  [ai-stylist/page.tsx] AI 채팅으로 생성형 이미지 수정
        → 선택/수정된 이미지 URL → localStorage 저장
        → [simulation-complete/page.tsx]

결과 저장
    [simulation-complete/page.tsx]
    POST /api/simulate/save/ (multipart: before_image, after_image, makeup_name, hair_name, is_saved)
        → AnalysisSession 생성 (face_shape, skin_tone 등 분석 필드는 전부 null)
        + SimulationResult(is_saved=True, makeup_name, hair_name) DB 저장
        → 실제 AI 분석 없이 이미지 경로 + 스타일명만 기록하는 구조
        → authorized 가드 필수 (마운트 시 자동 호출 — JWT 준비 전 실행 방지)

마이홈 조회
    [my-home/page.tsx]
    GET /api/saved-results/
        → is_saved=true인 본인 결과 목록 반환

관리자 대시보드
    [admin/page.tsx]
    GET /api/admin/dashboard/
        → 사용자 수, 세션 수, 피부톤/얼굴형 분포 반환
```

---

## 10. HairFastGAN 서버 배포 시 주의사항 (RTX 2080Ti)

로컬(CPU)에서 개발 후 서버로 이전할 때 `backend/gan_models/HairFastGAN-p310/` 내 파일 2개를 수동 복구해야 함.

| 파일 | 수정 내용 |
|------|-----------|
| `models/FeatureStyleEncoder/configs/001.yaml` | `device: 'cpu'` → `'cuda'` |
| `models/sean_codes/models/pix2pix_model.py` | `gpu_ids=[]` → `[0]` |

나머지 GPU 관련 코드는 `torch.cuda.is_available()` 자동 감지로 처리되므로 별도 수정 불필요.

---


## 12. 향후 확장 포인트

- **페이지네이션 UI**: 관리자 페이지 목록에서 20개 초과 시 페이지 버튼 추가
- **배포**: 프론트엔드 Vercel, 백엔드 EC2, DB RDS(MariaDB)
- **남성 메이크업 실제 이미지**: `/images/makeup/temp/` 경로에 실제 이미지 파일 추가 필요
- **`refs[:1]` 제거**: `backend/app/hair/services.py` 테스트용 코드 — 프로덕션 배포 전 반드시 삭제

---

## 13. 트러블슈팅

### [2026-06-09] 관리자 페이지

#### ① `items.map is not a function` — 스타일 관리, 사용자 관리

**원인:** `settings.py`에 `DEFAULT_PAGINATION_CLASS = PageNumberPagination`, `PAGE_SIZE = 20` 설정이 있어 모든 ViewSet 응답이 배열이 아닌 `{ count, next, previous, results: [...] }` 구조로 반환됨

**해결:** `r.data` → `r.data.results ?? r.data` 로 처리
```ts
api.get('/admin/hair-styles/').then((r) => setItems(r.data.results ?? r.data));
```

---

#### ② admin 로그인 후 관리자 페이지 대신 메인 페이지로 이동

**원인:** `handleSubmit`에서 `login()` 호출 후 `router.push('/admin')` 실행, 이후 React 리렌더 시 `useEffect`가 `router.replace('/')` 로 덮어씀 (두 곳에서 이동 명령이 충돌)

**해결:** `handleSubmit`의 `router.push` 제거, `useEffect` 한 곳에서만 role 기반 리다이렉트
```ts
useEffect(() => {
  if (isLoggedIn) router.replace(user?.role === 'admin' ? '/admin' : '/');
}, [isLoggedIn, user, router]);
```

---

### [이전 세션 — 2026-06-08] DB 연결 및 JWT 구현

#### ③ DB 접속 오류 — `Access denied to styleflowDB`
**원인:** DB 이름 대소문자 불일치 (`styleflowDB` → `styleflowdb`)  
**해결:** `.env`의 `DB_NAME` 수정

#### ④ `migrate` 실패 — `Table 'analysis_sessions' already exists`
**원인:** 원격 DB에 테이블이 미리 생성되어 있었고 `django_migrations`는 비어있는 상태  
**해결:** `python manage.py migrate --fake-initial`

#### ⑤ `simulate_makeup` 500 오류 — `'User' has no attribute 'is_authenticated'`
**원인:** 커스텀 `User`가 `models.Model`만 상속해 DRF `IsAuthenticated`가 요구하는 `is_authenticated` 속성이 없음  
**해결:** `User` 모델에 `@property is_authenticated(self): return True` 추가

#### ⑥ 로그인 후 Header가 갱신되지 않음
**원인:** `Header`는 layout에 마운트되어 route 변경 시 리렌더 안 됨, 커스텀 이벤트 방식으로 임시 처리했다가 근본 해결  
**해결:** `AuthContext` (React Context) 적용 — 전역 상태 변경 시 자동 리렌더

---

### [전반] 프론트엔드 localStorage 키 목록

페이지 간 데이터를 백엔드 없이 전달할 때 사용하는 브라우저 저장소 키.

| 키 | 내용 | 삭제 시점 |
|----|------|----------|
| `styleflow_face_image` | 업로드한 얼굴 사진 (압축 JPEG dataURL) | 없음 (덮어씀) |
| `styleflow_analysis_result` | `/analyze/` 전체 응답 JSON (hair/makeup_mappings 포함) | 없음 (덮어씀) |
| `styleflow_makeup_results` | GAN 결과 3장 `[{id, image, name}]` | 시뮬레이션 시작 / 최종 확정 |
| `styleflow_selected_id` | 선택된 결과 카드 id | 최종 확정 |
| `styleflow_selected_makeup_image` | 메이크업 확정 이미지 (헤어 단계 Before 입력용) | 최종 확정 |
| `styleflow_consultation` | AI 상담 진입 시 context (style, mappings 등) | 없음 (덮어씀) |
| `styleflow_hair_results` | 헤어 GAN 결과 3장 `[{id, image, name}]` | 시뮬레이션 시작 / 최종 확정 |
| `styleflow_final_result` | `{beforeImage, afterImage, completedStyles, styleNames:{makeup,hair}}` | 없음 (덮어씀) |

흐름: `/upload` → `styleflow_face_image` + `styleflow_analysis_result` 저장 → `/result/face` → `/simulation-flow` → `styleflow_makeup_results` 저장 → `/simulation-complete` → `styleflow_final_result` 저장

---

### [전반] BeautyGAN TF 추론 직렬화 (`threading.Lock`)

`backend/api/beautygan_service.py`에 `threading.Lock()`이 적용되어 있음.

**이유:** React StrictMode가 개발 모드에서 `useEffect`를 두 번 실행 → API가 동시에 두 번 호출됨 → 두 스레드가 동시에 `tf.reset_default_graph()`를 호출하면 TF 상태 충돌로 서버 크래시 발생.

- **프론트**: `simulation-flow/page.tsx`의 `apiCalledRef`로 두 번째 호출 차단
- **백엔드**: `threading.Lock()`으로 TF 추론 직렬화

Lock을 제거하면 개발 모드에서 서버가 크래시될 수 있으므로 유지 필요.

---

### [2026-06-11] 토큰 만료 시 메이크업 시뮬레이션 401 오류

#### ⑦ access token 만료 후 메이크업 시뮬레이션 401 — 자동 갱신 안 됨

**원인:** `simulation-flow/page.tsx`의 메이크업 API 호출이 `lib/api.ts`의 axios 인스턴스 대신 네이티브 `fetch()`를 직접 사용해 인터셉터를 우회함

**해결:** `fetch()` → `api.post()` 로 교체 (`simulation-flow/page.tsx`)

**핵심 규칙 — API 호출 시 반드시 `lib/api.ts` 인스턴스 사용:**
```ts
// ✅ 올바름 — 인터셉터 통과 (토큰 자동 갱신, 401 시 로그아웃 처리)
import api from "@/lib/api";
api.post("/simulate/makeup/", formData);

// ❌ 잘못됨 — 인터셉터 우회, 토큰 만료 시 그냥 401 반환
fetch("http://localhost:8000/api/simulate/makeup/", { headers: { Authorization: `Bearer ${token}` } });
```

`lib/api.ts` 인터셉터가 하는 일:
1. 401 응답 시 refresh token으로 access token 자동 갱신
2. 갱신 성공 → 원래 요청 재시도
3. 갱신 실패 → `clearAuth()` + `/login` 리다이렉트
4. `_retry` 플래그로 무한 루프 방지

---

### [2026-06-18] RAG 메이크업 필터 수정 + DB style_code 추가 + 피드백 저장 개선

#### ① 메이크업 RAG 결과가 항상 비어 있던 문제

**원인:** `views.py`에서 ChromaDB로 넘기는 필터 값 4개가 모두 실제 메타데이터와 불일치했음.

| 필터 필드 | 기존 (잘못된 값) | 수정 후 (ChromaDB 실제 값) |
|-----------|-----------------|--------------------------|
| `gender` | `'female'` (영문) | `'여성'` (한국어) |
| `face_shape` | `'round'` (영문) | `'둥근형'` (한국어) |
| `personal_color` | `'spring'` (영문) | `'봄웜'` (한국어) |
| `face_proportion` | `'golden'` (영문) | `'균형'` (한국어) |

**해결:** `views.py`에 4개 매핑 딕셔너리 추가, `analyze` 뷰에서 변환 후 RAG에 전달.

```python
_FACE_PROPORTION_MAP = {'upper': '상안부_긴형', 'middle': '중안부_긴형', 'lower': '하안부_긴형', 'golden': '균형'}
_PERSONAL_COLOR_MAP  = {'spring': '봄웜', 'summer': '여름쿨', 'fall': '가을웜', 'winter': '겨울쿨'}
_GENDER_MAP          = {'female': '여성', 'male': '남성'}
_FACE_SHAPE_MAP      = {'round': '둥근형', 'oval': '계란형', 'square': '각진형', 'heart': '역삼각형', 'long': '장방형'}
```

---

#### ② `MakeupStyle` 모델에 `style_code` 필드 추가

**배경:** RAG의 `_result_contains_style()`이 `style_code` 우선으로 매칭하도록 설계되어 있어, DB에도 코드가 있어야 정확한 추적이 가능함.

**마이그레이션 순서:**

| 파일 | 내용 |
|------|------|
| `0004_makupstyle_style_code.py` | `MakeupStyle`에 `style_code CharField(max_length=20, null=True, unique=True)` 추가 |
| `0005_makeup_styles_seed.py` | 16개 스타일 코드 시드 (`get_or_create` 사용) |
| `0006_makeup_styles_dedup.py` | 시드 시 발생한 중복 row 정리 (style_code=None 인 기존 row에 코드 채움) |

**주의:** `0005`에서 `get_or_create(style_code=item['style_code'])`를 쓰면 기존 row(style_code=None)는 갱신되지 않고 새 row가 생겨 32개로 중복됨 → `0006`에서 style_code가 있는 새 row를 삭제하고 기존 row를 `style_name` 기준으로 UPDATE.

**16개 스타일 코드 매핑:**

| style_name | style_code |
|------------|------------|
| 코랄 메이크업 | mk-sp-coral |
| 피치 메이크업 | mk-sp-peach |
| 주시 메이크업 | mk-sp-juicy |
| 듀이 메이크업 | mk-su-dewy |
| 내추럴 메이크업 | mk-su-natural |
| 로즈 메이크업 | mk-su-rose |
| 브라운 메이크업 | mk-au-brown |
| 시크 메이크업 | mk-au-chic |
| 오피스 메이크업 | mk-au-office |
| 버건디 메이크업 | mk-wi-burgundy |
| 글램 메이크업 | mk-wi-glam |
| 레드 메이크업 | mk-wi-red |
| 봄웜 내추럴 메이크업 | mk-m-sp-natural |
| 여름쿨 클린 메이크업 | mk-m-su-clean |
| 가을웜 소프트 메이크업 | mk-m-au-soft |
| 겨울쿨 샤프 메이크업 | mk-m-wi-sharp |

---

#### ③ `user_feedback.applied_style_key` 저장 구현

**목적:** 유저가 AI 상담 시 어떤 스타일(헤어/메이크업)에 대해 상담했는지 스타일 코드로 추적.

**데이터 흐름:**

```
[analyze API 응답]
    makeup_mappings: [{ id, style_name, style_code, image_url }]  ← style_code 추가
    hair_mappings:   [{ id, style_name, style_code, image_url }]  ← 기존부터 있었음

[simulation-flow/page.tsx - handleConsult()]
    styleflow_consultation에 hairMappings, makeupMappings (style_code 포함) 저장

[ai-stylist/page.tsx - applyApiResponse()]
    target_type에 따라 hairMappings[0] 또는 makeupMappings[0]의 style_code 추출
    → POST /feedback/chat/ 에 applied_style_key로 전송

[feedback_chat view]
    applied_style_key → UserFeedback.applied_style_key 저장
```

**수정 파일:**
- `backend/app/core/views.py` — `analyze` 뷰의 `makeup_mappings`에 `style_code` 포함, `feedback_chat` 뷰에서 `applied_style_key` 읽어 저장
- `frontend/app/simulation-flow/page.tsx` — `analysisResult` 타입에 `style_code?: string` 추가
- `frontend/app/ai-stylist/page.tsx` — `ConsultData` 타입 업데이트, `applyApiResponse`에서 `applied_style_key` 추출 후 전송

---

#### ④ `simulation-complete` 페이지 — SimulationResult 자동 생성 + 저장 분리

**문제:** "결과 저장" 버튼을 누르기 전 "AI 상담하기"를 누르면 `simulation_result_id`가 null이어서 피드백과 시뮬레이션 결과 간 연결이 끊어짐.

**해결 (Option A — 페이지 마운트 시 자동 기록):**

```
simulation-complete 페이지 마운트
    ↓
POST /api/simulate/save/ (is_saved=false)   ← 자동 호출
    → SimulationResult 생성 (마이홈 미노출)
    → savedSimResultId 상태에 저장

"결과 저장" 클릭
    → PATCH /api/simulate/save/{id}/
    → is_saved=True로 업데이트 → 마이홈에 노출
    → 버튼 "저장됨"으로 변경 + 비활성화

"AI 상담하기" 클릭
    → simulation_result_id = 항상 유효한 값 보장
```

**수정 내용:**

- `backend/app/core/views.py`
  - `simulate_save`: `is_saved` 파라미터 추가 (기본 `false`, `'false'`·`'0'`·`''` → False 처리)
  - `simulate_save_mark` 뷰 신규 추가 — PATCH로 `is_saved=True` 업데이트, 본인 소유 레코드만 허용

- `backend/app/core/urls.py`
  - `path('simulate/save/<int:pk>/', simulate_save_mark)` 추가

- `frontend/app/simulation-complete/page.tsx`
  - `autoSaveCalledRef`로 마운트 시 1회만 자동 POST 실행 (React StrictMode 이중 호출 방지)
  - `isSaved` 상태로 중복 저장 방지 및 버튼 UI 전환
  - `handleSave` → PATCH로 변경 (이미지 재전송 불필요)

---

### [2026-06-18] Gemini 이미지 생성형 수정 기능 추가 (rag-3 브랜치)

> Merge `main` → `rag-2` 이후 작업

#### ① 채팅으로 이미지 수정 요청 시 Gemini Vision으로 이미지 편집

**목적:** 유저가 채팅에서 "립 컬러를 코랄로 바꿔줘" 같이 이미지 수정을 요청하면 GAN 재처리 없이 Gemini imagen API로 즉시 편집 결과를 반환.

**처리 흐름:**

```
유저 채팅 입력 (이미지 수정 요청)
    ↓
LangGraph: INTENT_RETOUCH → analyze_retouch_request
    ↓
retouch_nodes.py: _download_image() — Django media 경로 or HTTP로 원본 이미지 바이트 취득
    ↓
_build_retouch_prompt() — target/requested_change → 자연어 프롬프트 생성
    ↓
google-genai SDK: Gemini imagen 모델 호출 (이미지 + 텍스트 → 편집 이미지)
    ↓
결과 이미지 → media/simulations/ 저장 → URL 반환
    ↓
프론트엔드: retouched_image_url → 채팅창에 리터칭 이미지 말풍선 표시
```

**수정 파일:**
- `backend/app/rag/chatbot_rag/retouch_nodes.py` — `_download_image()`, `_build_retouch_prompt()`, Gemini 호출 로직 추가
- `backend/app/rag/rag_core/config.py` — `GEMINI_API_KEY`, `GEMINI_IMAGE_MODEL` 상수 추가
- `backend/app/core/views.py` — `retouched_image_url` 응답 필드 반환

**로컬 이미지 경로 최적화:**
```python
# HTTP 라운드트립 없이 Django media 파일 직접 읽기
if url.startswith(media_url):
    local_path = os.path.join(media_root, url[len(media_url):])
# http://localhost:8000/media/... 형태도 처리
for host in ("http://127.0.0.1:8000", "http://localhost:8000", ...):
    if url.startswith(host + media_url):
        local_path = ...
```

---

#### ② LangGraph 라우팅 분기 수정 — 이미지 수정 확인 흐름 버그 수정

**문제:** `PENDING_RETOUCH_CONFIRMATION` 조건에 `and selected_option` 가드가 있어 유저가 확인 버튼을 누르지 않으면 라우팅이 빠져나가지 못하는 버그.

**해결:** 조건에서 `selected_option` 가드 제거.

```python
# 수정 전
if pending == PENDING_RETOUCH_CONFIRMATION and selected_option:
    return "handle_retouch_confirmation"

# 수정 후
if pending == PENDING_RETOUCH_CONFIRMATION:
    return "handle_retouch_confirmation"
```

---

#### ③ 새 인텐트 노드 추가 — 대화 기억 조회 / 후속 추천

**추가된 인텐트:**

| 인텐트 상수 | 설명 | 라우팅 노드 |
|-------------|------|-------------|
| `INTENT_MEMORY_RECALL` | "아까 추천해준 스타일이 뭐야?" 등 이전 대화 참조 | `answer_memory_recall` |
| `INTENT_FOLLOWUP_RECOMMENDATION` | 추천 후 추가 질문 (다른 옵션, 이유 설명 등) | `answer_followup_recommendation` |

**라우팅 우선순위 (route_after_intent):**
```
INTENT_MEMORY_RECALL (최우선)
    → answer_memory_recall

INTENT_RETOUCH
    → analyze_retouch_request

INTENT_FOLLOWUP_RECOMMENDATION (needs_clarification보다 먼저)
    → answer_followup_recommendation

...이하 기존 순서
```

**수정 파일:**
- `backend/app/rag/chatbot_rag/graph.py` — 노드 등록 + 라우팅 분기 추가
- `backend/app/rag/chatbot_rag/intents.py` — 상수 추가
- `backend/app/rag/chatbot_rag/intent_keywords.py` — 키워드 확장
- `backend/app/rag/chatbot_rag/intent_classifier.py` — 분류 로직 수정
- `backend/app/rag/chatbot_rag/nodes.py` — `answer_followup_recommendation`, `answer_memory_recall` 노드 구현
- `backend/app/rag/chatbot_rag/memory.py` — 대화 기억 참조 로직 추가

---

#### ④ `sentence-transformers` 버전 충돌 수정

**문제:** `sentence-transformers==5.6.0`이 `huggingface-hub>=1.0` 런타임 체크를 수행하는데, 현재 환경의 `huggingface-hub` 버전과 충돌하여 임포트 오류 발생.

**해결:** 버전 다운그레이드 + 관련 패키지 고정.

```
# requirements.txt 변경
sentence-transformers: 5.6.0 → 3.0.1
transformers: 4.44.2  (신규 고정)
tokenizers: 0.19.1    (신규 고정)
```

**추가 수동 조치 필요 (설치 후 1회):**
`transformers==4.44.2`가 `huggingface-hub` 버전을 런타임에 체크하므로 아래 파일에서 해당 항목을 수동 제거해야 함:
```
anaconda3/envs/p310_pj_styleflow/Lib/site-packages/transformers/dependency_versions_check.py
→ pkgs_to_check_at_runtime 리스트에서 "huggingface-hub" 줄 삭제
```

---

### [2026-06-20] Face_Analysis 통합 + 시뮬레이션 동적 레퍼런스

#### ① 헤어 gender 필터 — 같은 스타일명이 남/여 모두 존재

**문제:** "울프", "그런지" 등 스타일명이 남성(m-)과 여성(f-) DB에 모두 존재 → 잘못된 성별 스타일 참조.

**해결:** `hair_code__startswith` 필터로 성별 구분.
```python
hair_code_prefix = 'm-' if gender == 'male' else 'f-'
HairStyle.objects.filter(style_name=n, hair_code__startswith=hair_code_prefix).first()
```

---

#### ② 남성 메이크업 이미지 3장 구조

**배경:** 여성은 메이크업당 1장이지만 남성도 3장 결과를 보여줘야 함.

**해결:** `MakeupStyle.style_code`의 `unique=True` 제거, 남성 메이크업 4개 시즌별로 동일 style_code 행 3개씩 추가 (총 12행).

**migration:** `0007_remove_makeup_style_code_unique.py`

**views.py 분기:**
```python
if gender == 'male':
    makeup_style_objs = list(MakeupStyle.objects.filter(style_name=style_name))
else:
    obj = MakeupStyle.objects.filter(style_name=style_name).first()
    makeup_style_objs = [obj] if obj else []
```

---

#### ③ 시뮬레이션 동적 레퍼런스 이미지 — useEffect race condition

**문제:** `simulation-flow/page.tsx`에서 `analysisResult` 상태를 사용해 레퍼런스 이미지를 구성했으나 마운트 시 `setAnalysisResult()`가 아직 반영되지 않아 항상 null → 기존 하드코딩 이미지 사용.

**해결:** 상태 대신 localStorage 직접 파싱.
```ts
// ❌ 상태 사용 (null일 수 있음)
const refs = (analysisResult?.makeup_mappings ?? [])...

// ✅ localStorage 직접 파싱 (항상 동기 읽기)
const raw = localStorage.getItem("styleflow_analysis_result");
const ar = raw ? JSON.parse(raw) : null;
const refs = (ar?.makeup_mappings ?? [])...
```

**백엔드 연동:**
- `makeup/views.py`, `hair/views.py`: `reference_images` JSON 파싱 후 service로 전달
- `makeup/services.py`, `hair/services.py`: `_resolve_reference_images()` — `/images/...` URL → `frontend/public/` 로컬 경로 매핑, 없으면 REFERENCE_IMAGES 폴백

---

#### ④ result 페이지 UI 개선

- 헤어 카드 이미지: `object-cover object-center` → `object-top` (머리카락 전체 노출)
- 헤어 카드 이름: `{style_name}` → `{style_name} 헤어` suffix 추가

---

### [2026-06-19] AI 채팅 응답 대기 중 타이핑 인디케이터 애니메이션 추가

**문제:** 유저가 메시지를 전송한 후 AI 응답이 생성되는 동안 (API 호출 + 800ms 딜레이) 채팅창에 아무런 피드백이 없어 응답이 오고 있는지 알 수 없는 UX 문제.

**해결:** 세 개의 점이 순차적으로 bouncing하는 타이핑 인디케이터를 AI 말풍선 자리에 표시.

**변경 파일:** `frontend/app/ai-stylist/page.tsx` (프론트엔드만 수정, 백엔드 변경 없음)

**구현 내용:**

| 항목 | 내용 |
|------|------|
| `TypingIndicator` 컴포넌트 | 회색 말풍선 + 세 점 `animate-bounce` (Tailwind, animation-delay로 순차 처리) |
| `isTyping` state | API 호출 시작~응답 표시 직전 구간을 추적 |
| 중복 전송 방지 | `handleSend`, `handleSelectOption` 진입 시 `isTyping`이면 즉시 return |
| 입력 비활성화 | `isTyping` 중 Input, 전송 버튼 `disabled` |
| 스크롤 연동 | `isTyping=true` 시 채팅 컨테이너 하단으로 자동 스크롤 |

**타이밍:**
```
유저 전송
  → setIsTyping(true)   ← 인디케이터 표시
  → API 호출 (수 초)
  → 응답 수신 → 800ms delay
  → setIsTyping(false) + setMessages(...)  ← 인디케이터 → AI 말풍선으로 교체
```

에러/폴백 경로에서도 동일하게 800ms 후 `setIsTyping(false)` 처리하여 인디케이터가 남지 않도록 함.

---

### [2026-06-21] UI 개선 + SimulationResult 스타일명 저장

#### ① 분석 로딩 UI — 6단계 + 모델명 표시 (`upload/page.tsx`)

사용자가 업로드 후 분석 대기 중 어떤 모델이 실행 중인지 확인할 수 있도록 단계별 텍스트 개선.

```ts
const analysisSteps = [
  "얼굴 영역 감지 중 (MediaPipe FaceMesh)",
  "얼굴형 분석 중 (LightGBM)",
  "피부톤 분석 중 (LightGBM)",
  "헤어스타일 추천 생성 중 (Rule-based)",
  "메이크업 추천 생성 중 (Rule-based)",
  "스타일 분석 리포트 생성 중 (RAG + Gemini)",
];
```

Loader2 스피너 + 순차 로딩 (`autoAdvance` 타이머 + `apiCallPromise` 완료 시 마지막 단계로 강제 진입) 구현.

---

#### ② 시뮬레이션 로딩 UI — 메이크업/헤어 별도 4단계 (`simulation-flow/page.tsx`)

```ts
const MAKEUP_LOADING_STEPS = [
  "얼굴 랜드마크 감지 중 (dlib)",
  "얼굴 마스크 추출 중 (MediaPipe FaceMesh)",
  "메이크업 합성 중 (BeautyGAN)",
  "최종 이미지 생성 중 (PostProcess)",
];
const HAIR_LOADING_STEPS = [
  "얼굴 임베딩 중 (e4e + BiSeNet)",
  "헤어 형태 합성 중 (SEAN + ShapeAdaptor)",
  "헤어 색상 적용 중 (CLIP Blending)",
  "최종 이미지 생성 중 (PostProcess)",
];
```

메이크업 단계 간격 4000ms, 헤어 단계 간격 8000ms.

`getMappingName` 방어 코드: 이미 "헤어"로 끝나는 이름에 suffix 중복 방지.
```ts
return category === "hair" && name && !name.endsWith("헤어")
  ? `${name} 헤어`
  : name;
```

---

#### ③ 헤어 색상 보존 — `color_img=source_path` (`backend/app/hair/services.py`)

HairFastGAN에서 레퍼런스 이미지의 헤어 색상을 그대로 적용하면 사용자 원본 머리색이 바뀌는 문제 발생.

**해결:** `color_img` 파라미터에 레퍼런스 이미지 대신 사용자 원본 이미지 경로(`source_path`)를 전달해 원본 머리색 유지.

```python
refs = _resolve_reference_images(reference_images) if reference_images else REFERENCE_IMAGES
refs = refs[:1]  # TODO: 테스트용 — 프로덕션 배포 전 제거
for ref in refs:
    # color_img=source_path: 레퍼런스가 아닌 사용자 원본 색상 유지
    result = pipeline(..., color_img=source_path, ...)
```

---

#### ④ 결과 페이지 업로드 사진 카드 높이 고정 (`result/[type]/page.tsx`)

**문제:** 왼쪽 업로드 사진 이미지가 CSS Grid 행 높이를 직접 밀어올려 오른쪽 카드 두 개 합친 높이보다 길어지는 레이아웃 깨짐.

**해결:** `position: absolute`로 이미지를 높이 계산에서 제외.

```tsx
<div className="lg:col-span-2 h-full">
  <Card className="h-full overflow-hidden border border-gray-200 flex flex-col">
    <div className="relative flex-1 overflow-hidden">
      <img
        src={faceImage || "/reference/makeup/MS1.png"}
        alt="업로드된 사진"
        className="absolute inset-0 w-full h-full object-cover"
      />
    </div>
    <div className="p-3 bg-gray-50 text-center flex-shrink-0">
      <span className="text-xs text-gray-400">업로드된 원본 사진</span>
    </div>
  </Card>
</div>
```

헤어 추천 카드 이미지: `object-contain`으로 변경 (머리 위쪽 잘림 방지).

---

#### ⑤ `simulation-complete` 자동 저장 401 수정

**원인:** 페이지 마운트 시 자동 저장 useEffect가 `authorized` 상태 확인 없이 즉시 실행 → JWT가 아직 준비되기 전 API 호출 → 401 Unauthorized.

**해결:** `!authorized` 가드 추가.

```tsx
useEffect(() => {
  if (!authorized || !finalResult || autoSaveCalledRef.current) return;
  autoSaveCalledRef.current = true;
  // ... POST /api/simulate/save/
}, [finalResult, authorized]);
```

---

#### ⑥ SimulationResult 스타일명 텍스트 필드 추가 (마이홈 스타일명 표시)

**문제:** `simulate_save` 뷰가 `hair_mapping`/`makeup_mapping` FK를 저장하지 않아 시리얼라이저의 `appliedStyles`가 항상 빈 배열로 반환됨 → 마이홈 카드에 스타일명 미표시.

**해결:** FK 대신 스타일명 문자열 필드 직접 저장.

`backend/app/models.py` — 필드 추가:
```python
makeup_name = models.CharField(max_length=100, blank=True, default='')
hair_name = models.CharField(max_length=100, blank=True, default='')
```

`backend/app/core/views.py` — `simulate_save` 뷰에서 저장:
```python
sim = SimulationResult(
    user_id=request.user.id,
    analysis_session=session,
    is_saved=is_saved,
    generated_image_path=f'simulations/{after_image_filename}',
    makeup_name=request.data.get('makeup_name', ''),
    hair_name=request.data.get('hair_name', ''),
)
```

`backend/app/core/serializers.py` — FK null 시 텍스트 필드 폴백:
```python
makeup_name = (instance.makeup_mapping.style_name if instance.makeup_mapping else None) or instance.makeup_name
hair_name = (instance.hair_mapping.style_name if instance.hair_mapping else None) or instance.hair_name
if makeup_name:
    applied_styles.append({'type': 'makeup', 'name': makeup_name})
if hair_name:
    applied_styles.append({'type': 'hair', 'name': hair_name})
data['appliedStyles'] = applied_styles
```

**마이그레이션 실행 필요:**
```bash
python manage.py makemigrations
python manage.py migrate
```

---

#### ⑦ 마이홈 Before/After UI 개선 (`my-home/page.tsx`)

- Before 이미지 컨테이너: `w-2/5 flex-shrink-0` → `flex-1` (After와 동일 비율로 양분)
- 구분 화살표: `left-2/5` → `left-1/2 -translate-x-1/2` (정중앙 정렬)

스타일명 표시:
```ts
const STYLE_SUFFIX: Partial<Record<AppliedStyle["type"], string>> = {
  makeup: "메이크업",
  hair: "헤어",
};
const getDisplayName = (style: AppliedStyle): string => {
  const suffix = STYLE_SUFFIX[style.type];
  if (!suffix || style.name.endsWith(suffix)) return style.name;
  return `${style.name} ${suffix}`;
};
```

---

#### ⑧ face_analysis 통합 확인

루트의 `Face_Analysis/` 폴더는 삭제 완료 (수동). 실제 코드는 `backend/app/face_analysis/`에서 동작 중.

`backend/app/core/views.py`에서 sys.path 등록 후 직접 임포트:
```python
_FA_DIR = os.path.join(BASE_DIR, 'app', 'face_analysis')
if _FA_DIR not in sys.path:
    sys.path.insert(0, _FA_DIR)
from diagnose import diagnose as fa_diagnose
from Recommend import recommend as fa_recommend
```

더미 데이터는 예외 발생 시 폴백으로만 사용.
