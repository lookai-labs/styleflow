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
│       └── reference/
│           └── makeup/         ← 메이크업 스타일 미리보기 이미지 (MS1~3.png)
│                                  현재: 사용자 화면 표시 전용 정적 에셋
│                                  [향후] 분석 세션 기반 스타일 매핑 로직 추가 시,
│                                  MakeupStyle 모델에 gan_image_path 필드를 추가해
│                                  백엔드 gan_models 경로와 DB를 연결하는 구조로 통합 예정.
│                                  그 시점에 이 미리보기 이미지도 MakeupStyle.image_url
│                                  하나로 통합 가능
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
    │   └── makeup/             ← BeautyGAN
    │       ├── views.py        ← simulate_makeup
    │       ├── urls.py
    │       └── services.py
    ├── gan_models/
    │   ├── HairFastGAN-p310/
    │   │   └── imgs/
    │   │       └── hair/       ← HairFastGAN 레퍼런스 이미지 (MH1~3.jpg)
    │   └── BeautyGAN-master-p310/
    │       └── imgs/
    │           └── makeup/     ← BeautyGAN 레퍼런스 이미지 (MS1~3.png)
    │                              현재: services.py에 REFERENCE_IMAGES로 하드코딩
    │                              [향후] 스타일 매핑 로직 추가 시 MakeupStyle.gan_image_path
    │                              필드로 DB에서 경로를 관리하도록 변경 예정
    ├── media/                  ← 런타임 생성 (MEDIA_ROOT, git 제외)
    │   ├── analyses/           ← 사용자가 업로드한 원본 사진
    │   └── simulations/        ← GAN 결과 이미지
    ├── styleflow/
    │   ├── settings.py
    │   └── urls.py
    ├── manage.py
    ├── requirements.txt
    ├── .env
    └── .env.example
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
| POST | `/simulate/makeup/` | BeautyGAN 메이크업 시뮬레이션 |
| POST | `/simulate/save/` | 시뮬레이션 결과 저장 |
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
| GET | `/users/` | 전체 사용자 목록 |
| GET | `/analyses/` | 분석 세션 목록 (`?user_id=`, `?anomaly=true`) |
| GET | `/simulation-results/` | 시뮬레이션 결과 목록 |
| DELETE | `/simulation-results/{id}/` | 결과 삭제 |
| GET | `/style-mappings/` | 추천 결과 목록 |

> **페이지네이션**: 모든 목록 API는 `{ count, next, previous, results: [...] }` 형태로 반환 (PAGE_SIZE=20)

---

## 6. Django 데이터베이스 모델 (7개 테이블)

```python
class User                # users — nickname, password, gender, role, created_at
class HairStyle           # hair_styles — hair_code, style_name, image_url
class MakeupStyle         # makeup_styles — style_name, image_url
class AnalysisSession     # analysis_sessions — user_id, image_path, face_shape, face_point,
                          #   skin_tone, skin_lab_b, ratio_*, result(JSON), created_at
class StyleMappingList    # style_mapping_list — user_id, analysis_session_id, type,
                          #   hair_style_id, makeup_style_id, style_name, created_at
class SimulationResult    # simulation_results — user_id, analysis_session_id,
                          #   hair_mapping_id, makeup_mapping_id,
                          #   generated_image_path, is_saved, created_at
class UserFeedback        # user_feedback — user_id, simulation_result_id,
                          #   target_type, feedback_text, applied_style_key, created_at
```

**주의:** `User`는 `models.Model`만 상속 (AbstractBaseUser 미사용)  
DRF `IsAuthenticated` 호환을 위해 `is_authenticated = property(lambda self: True)` 직접 추가

---

## 6-1. BeautyGAN 메이크업 시뮬레이션

TensorFlow 2.13 기반 BeautyGAN 모델로 원본 사진에 메이크업 전이.

**실행 환경:** conda `p311t213_styleflow_test`

**처리 흐름:**
```
원본 이미지
    ↓ dlib — 얼굴 감지 + 5점 랜드마크 → 256×256 chip 추출
    ↓ BeautyGAN TF 세션 — 레퍼런스 메이크업 이미지와 쌍으로 추론
    ↓ mediapipe FaceMesh — 원본 해상도 얼굴 마스크 생성
    ↓ Affine 역변환 + Feathered 블렌딩 → 원본 해상도 결과 이미지
```

**레퍼런스 메이크업** (imgs/makeup/):
| 파일 | 스타일명 |
|------|----------|
| MS1.png | 웜 코랄 메이크업 |
| MS2.png | 소프트 뉴트럴 |
| MS3.png | 로즈 글로우 |

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

### 백엔드 requirements.txt
```
numpy==1.24.3
tensorflow==2.13.0
dlib==19.24.2
opencv-contrib-python==4.8.1.78
mediapipe==0.10.9
Django==5.2.14
djangorestframework==3.17.1
django-cors-headers==4.9.0
python-dotenv==1.2.2
mysqlclient==2.2.8
Pillow==12.2.0
djangorestframework-simplejwt==5.4.0
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
# BeautyGAN 전용 conda 환경 활성화 필수
conda activate p311t213_styleflow_test

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

사진 업로드 + 시뮬레이션
    [upload/page.tsx] → StylingSelectionModal에서 시뮬레이션 유형 선택
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
    POST /api/simulate/save/ (multipart)
        → AnalysisSession 생성 (face_shape, skin_tone 등 분석 필드는 전부 null)
        + SimulationResult(is_saved=True) DB 저장
        → 실제 AI 분석 없이 이미지 경로만 기록하는 구조

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

## 11. DB 연동 시 이미지 경로 정리 유의사항

현재 스타일 레퍼런스 이미지가 두 곳에 중복 관리되고 있음.

| 위치 | 용도 |
|------|------|
| `frontend/public/reference/makeup\|hair/` | 프론트 FALLBACK_RESULTS 미리보기용 |
| `backend/gan_models/.../imgs/makeup\|hair/` | GAN 추론 레퍼런스용 |

**DB 연동 후 개선 방향:**
- 이미지를 Django `media/styles/`에 한 번만 업로드
- DB `MakeupStyle.image_url` / `HairStyle.image_url` 에 해당 URL 저장
- 백엔드: `MEDIA_ROOT` 기준 파일시스템 경로로 GAN에 전달
- 프론트엔드: `image_url` (URL)을 미리보기에 직접 사용
- 이 시점에 `frontend/public/reference/` 정적 이미지와 `backend/.../imgs/` 중복 제거 가능

---

## 12. 향후 확장 포인트

- **실제 AI 얼굴 분석 연동**: 업로드 후 face_shape, skin_tone 등 자동 분석
- **스타일 추천 로직**: analysis_sessions 결과 기반으로 style_mapping_list 자동 생성
- **페이지네이션 UI**: 관리자 페이지 목록에서 20개 초과 시 페이지 버튼 추가
- **배포**: 프론트엔드 Vercel, 백엔드 EC2, DB RDS(MariaDB)
- **마이홈 appliedStyles**: 현재 스타일명 미표시 (의도적 보류) — 저장 시 `StyleMappingList` 레코드 생성 후 `SimulationResult.makeup_mapping` FK 연결 필요. serializer가 `makeup_mapping=None`이면 `appliedStyles: []` 반환.
- **HairFastGAN 연동**: 모델 미준비로 제외된 상태. 이식 작업 순서:
  1. `backend/api/hairgan_service.py` 작성 (`beautygan_service.py`와 동일 구조)
  2. `POST /api/simulate/hair/` 엔드포인트 추가 (`views.py`, `urls.py`)
  3. 헤어 레퍼런스 이미지 3장을 `frontend/public/reference/hair/`에 추가
  4. `simulation-flow/page.tsx` 로딩 useEffect `else` 브랜치를 실제 API 호출로 교체
  5. `StylingSelectionModal`에서 헤어 선택지 활성화

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
| `styleflow_makeup_results` | GAN 결과 3장 `[{id, image, name}]` | 시뮬레이션 시작 / 최종 확정 |
| `styleflow_selected_id` | 선택된 결과 카드 id | 최종 확정 |
| `styleflow_final_result` | `{beforeImage, afterImage, completedStyles}` | 없음 (덮어씀) |

흐름: `/upload` → `styleflow_face_image` 저장 → `/simulation-flow` → `styleflow_makeup_results` 저장 → `/simulation-complete` → `styleflow_final_result` 저장

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
