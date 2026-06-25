# StyleFlow

> AI 기반 얼굴형·퍼스널컬러 분석 및 헤어·메이크업 시뮬레이션 서비스

![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)
![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-4-38B2AC?logo=tailwind-css)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python)
![MariaDB](https://img.shields.io/badge/MariaDB-003545?logo=mariadb)

---

## 소개

StyleFlow는 사용자 얼굴 사진 한 장으로 얼굴형·피부톤을 자동 분석하고, AI가 적합한 헤어스타일과 메이크업을 추천한 뒤 GAN 모델로 실제로 합성해 보여주는 뷰티 시뮬레이션 서비스입니다.

추천 결과에 대해 RAG 기반 AI 스타일리스트 챗봇으로 피드백 상담을 받을 수 있으며, Gemini Vision을 통해 채팅으로 합성 이미지를 직접 수정하는 기능도 제공합니다.

---

## 데모

> 스크린샷 / GIF 추가 예정

---

## 주요 기능

### 1. AI 얼굴 분석
사용자가 업로드한 얼굴 사진을 기반으로 얼굴형, 삼정 비율, 퍼스널컬러를 자동 진단합니다.

- **얼굴 감지**: MediaPipe FaceMesh — 468개 랜드마크 추출
- **얼굴형 분류**: LightGBM 모델 — 계란형, 둥근형, 각진형, 역삼각형, 장방형
- **퍼스널컬러 분류**: LightGBM 모델 — 봄웜, 여름쿨, 가을웜, 겨울쿨

### 2. 헤어 · 메이크업 시뮬레이션
분석 결과 기반으로 추천된 스타일을 실제 얼굴에 합성합니다.

- **메이크업 합성**: BeautyGAN (TensorFlow 2.13) — 레퍼런스 메이크업 이미지의 색상/질감을 사용자 얼굴에 자연스럽게 전이
- **헤어 합성**: HairFastGAN (PyTorch) — 레퍼런스 헤어스타일을 얼굴형에 맞게 정렬 후 합성
- 결과 이미지 3장 중 원하는 1장 선택 가능

### 3. AI 스타일리스트 챗봇
추천받은 헤어·메이크업에 대해 자연어로 상담할 수 있는 RAG 기반 챗봇입니다.

- **LangGraph** 기반 멀티 인텐트 그래프 라우팅
- **ChromaDB** 벡터 검색으로 스타일 관련 문서 참조
- **Gemini** LLM으로 얼굴형·퍼스널컬러 기반 맞춤 답변 생성
- 지원 인텐트: 어울림 판단, 손질 방법, 유지 관리, 스타일 비교, 무드 선택, 의상 코디 추천 등

### 4. Gemini Vision 이미지 리터치
채팅 메시지로 합성 이미지를 직접 수정할 수 있습니다.

- "립 컬러를 코랄로 바꿔줘", "앞머리를 내려줘" 등 자연어 수정 요청 처리
- Gemini imagen API로 이미지 편집 후 결과를 채팅창에 즉시 표시

### 5. 의상 코디 추천
분석된 헤어·메이크업 스타일을 바탕으로 상황별 의상 조합을 추천합니다.

- 면접, 결혼식 하객, 데이트, 출근, 데일리 등 상황별 추천
- 퍼스널컬러와 조화되는 색상 및 아이템 조합 제안

### 6. 마이홈 & 관리자 대시보드
- **마이홈**: 저장한 Before/After 시뮬레이션 결과와 적용 스타일명 조회
- **관리자**: 사용자·스타일·세션·추천 결과 관리 및 통계 대시보드

---

## 시스템 아키텍처

```
사용자
  │
  ▼
┌─────────────────────────────────┐
│       Next.js 15 (Frontend)     │
│  App Router + Tailwind + shadcn │
└────────────────┬────────────────┘
                 │ REST API (JWT)
                 ▼
┌─────────────────────────────────┐
│       Django 5.2 (Backend)      │
│   DRF + simplejwt + MariaDB     │
│                                 │
│  ┌──────────┐  ┌─────────────┐  │
│  │ analyze  │  │  simulate   │  │
│  │  Face    │  │  Hair /     │  │
│  │ Analysis │  │  Makeup     │  │
│  └────┬─────┘  └──────┬──────┘  │
│       │               │         │
│  ┌────▼─────┐  ┌──────▼──────┐  │
│  │ LightGBM │  │  HairFast   │  │
│  │ MediaPipe│  │  GAN /      │  │
│  │ (진단)   │  │  BeautyGAN  │  │
│  └──────────┘  └─────────────┘  │
│                                 │
│  ┌──────────────────────────┐   │
│  │       RAG Module         │   │
│  │  LangGraph + ChromaDB    │   │
│  │  + Gemini (챗봇 / 리터치)│   │
│  └──────────────────────────┘   │
└─────────────────────────────────┘
                 │
                 ▼
          MariaDB (원격)
```

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| **Frontend** | Next.js 15 (App Router), TypeScript, Tailwind CSS 4, shadcn/ui, Axios |
| **Backend** | Django 5.2, Django REST Framework, djangorestframework-simplejwt |
| **Database** | MariaDB |
| **얼굴 분석** | MediaPipe FaceMesh, dlib, LightGBM, scikit-learn, OpenCV |
| **헤어 합성** | HairFastGAN (PyTorch 1.13), CLIP, e4e Encoder, BiSeNet |
| **메이크업 합성** | BeautyGAN (TensorFlow 2.13), dlib, MediaPipe |
| **RAG / 챗봇** | LangGraph, ChromaDB, sentence-transformers, LangChain, Google Gemini |
| **이미지 편집** | Google Gemini Vision (imagen API) |
| **인증** | JWT (access 1h / refresh 7d) |
| **환경** | Conda (Python 3.10), Node.js |

---

## 서비스 흐름

```
1. 회원가입 / 로그인
        ↓
2. 얼굴 사진 업로드
        ↓
3. AI 분석 (얼굴형 + 삼정 비율 + 퍼스널컬러)
        ↓
4. 헤어·메이크업 스타일 추천 결과 확인
        ↓
5. 시뮬레이션 선택 (메이크업만 / 헤어만 / 둘 다)
        ↓
6. GAN 합성 결과 3장 중 1장 선택
        ↓
7. (선택) AI 스타일리스트 챗봇으로 피드백 / 이미지 수정
        ↓
8. 결과 저장 → 마이홈에서 Before/After 확인
```

---

## 로컬 실행 방법

### 사전 준비

- Node.js 18+
- Anaconda (Python 3.10 환경)
- MariaDB 접속 정보 (`.env` 파일 필요)

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### 백엔드

```bash
# conda 환경 활성화
conda activate p310_pj_styleflow

# 의존성 설치 (루트 requirements.txt 기준)
pip install -r requirements.txt

cd backend

# 마이그레이션
python manage.py migrate

# 개발 서버 실행 (--noreload 필수 — TensorFlow 세션 중복 로드 방지)
python manage.py runserver --noreload
# → http://localhost:8000
```

### 환경 변수 설정

`backend/.env` 파일 생성 후 아래 내용 입력:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.mysql
DB_NAME=styleflowdb
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=your-db-host
DB_PORT=3306

CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## 팀원

> 역할 분담 추가 예정

---

## 주요 기술적 도전

| 문제 | 해결 방법 |
|------|----------|
| BeautyGAN TF 세션 동시 호출 충돌 | `threading.Lock()`으로 추론 직렬화 |
| JWT 만료 시 API 자동 갱신 누락 | 모든 API 호출을 `lib/api.ts` axios 인스턴스로 통일, 인터셉터에서 refresh 처리 |
| GAN 입력 레퍼런스 이미지 race condition | `useEffect` 상태 대신 localStorage 직접 파싱으로 동기 읽기 |
| ChromaDB 필터 언어 불일치 | 영문 진단값 → 한국어 매핑 딕셔너리 변환 후 RAG 전달 |
| 합성 후 저장 전 AI 상담 시 세션 연결 끊김 | 페이지 마운트 시 `is_saved=false`로 자동 기록, 저장 확정 시 PATCH로 상태 변경 |
