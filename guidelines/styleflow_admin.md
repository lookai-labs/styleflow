# StyleFlow 관리자 페이지 문서

## 현재 상태

| 항목 | 상태 |
|------|------|
| 프론트엔드 | ✅ 완료 |
| BeautyGAN 시뮬레이션 | ✅ 이식 완료 |
| DB / models.py | ✅ 완료 — ERD 기준 7개 테이블, 원격 MariaDB(220.80.16.79) 연결 |
| 로그인(JWT) | ✅ 완료 — 회원가입/로그인/토큰 갱신 구현 |
| 관리자 페이지 | ✅ 완료 — 1·2·3순위 전부 구현 |

---

## 관리자 페이지 구성

**방향:** Django admin UI X → **Next.js `frontend/app/admin/`** 에 구현  
- 기존 사이트 디자인(Tailwind + shadcn/ui) 동일하게 적용
- role='admin' 로그인 시 자동으로 /admin 리다이렉트
- Header가 관리자용으로 교체됨 (StyleFlow Admin + 로그아웃만 표시)

### 메뉴 구성 (사이드바 순서)

| 순서 | 메뉴 | 경로 | 설명 |
|------|------|------|------|
| 1 | 대시보드 | `/admin` | 전체 사용자 수, 분석 세션 수, 피부톤/얼굴형 분포 |
| 2 | 사용자 관리 | `/admin/users` | 전체 유저 목록, 분석 기록 모달 |
| 3 | 스타일 관리 | `/admin/styles` | hair_styles / makeup_styles CRUD |
| 4 | 피드백 관리 | `/admin/feedback` | 전체/헤어/메이크업 탭 필터 |
| 5 | 세션 검수 | `/admin/sessions` | 전체 세션 + 이상 데이터(null 필드) 탭 |
| 6 | 추천 결과 검수 | `/admin/mappings` | style_mapping_list, 타입별 탭 필터 |
| 7 | 시뮬레이션 결과 | `/admin/simulations` | simulation_results 목록, 삭제 |

---

## 관리자 전용 API 엔드포인트

| Method | URL | 설명 |
|--------|-----|------|
| GET | `/api/admin/dashboard/` | 통계 데이터 |
| GET/POST | `/api/admin/hair-styles/` | 헤어스타일 목록/추가 |
| GET/PUT/DELETE | `/api/admin/hair-styles/{id}/` | 헤어스타일 수정/삭제 |
| GET/POST | `/api/admin/makeup-styles/` | 메이크업스타일 목록/추가 |
| GET/PUT/DELETE | `/api/admin/makeup-styles/{id}/` | 메이크업스타일 수정/삭제 |
| GET | `/api/admin/feedback/` | 피드백 목록 (`?target_type=hair\|makeup`) |
| GET | `/api/users/` | 전체 사용자 목록 |
| GET | `/api/analyses/` | 분석 세션 목록 (`?user_id=`, `?anomaly=true`) |
| GET | `/api/simulation-results/` | 시뮬레이션 결과 목록 |
| DELETE | `/api/simulation-results/{id}/` | 결과 삭제 |
| GET | `/api/style-mappings/` | 추천 결과 목록 |

**권한:** 모든 관리자 API는 `IsAdmin` 퍼미션 클래스 적용 (role='admin' 필요)

---

## 관련 파일

### 백엔드
- `api/views.py` — `IsAdmin` 클래스, `HairStyleViewSet`, `MakeupStyleViewSet`, `UserFeedbackViewSet`, `admin_dashboard`
- `api/serializers.py` — `HairStyleSerializer`, `MakeupStyleSerializer`, `UserFeedbackSerializer` + 기존 serializer에 `user_nickname` 필드 추가
- `api/urls.py` — 관리자 전용 router 등록

### 프론트엔드
- `app/admin/layout.tsx` — 사이드바 + `useRequireAdmin` 적용
- `hooks/useRequireAdmin.ts` — 비관리자 접근 시 `/` 리다이렉트
- `components/Header.tsx` — `user.role === 'admin'`이면 관리자 헤더 렌더링

---

## 테이블 구조 (ERD)

```sql
-- 1. users
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    nickname VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    gender ENUM('male', 'female') NOT NULL,
    role ENUM('user', 'admin') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. hair_styles
CREATE TABLE hair_styles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    hair_code VARCHAR(5),
    style_name VARCHAR(100) NOT NULL,
    image_url VARCHAR(500)
);

-- 3. makeup_styles
CREATE TABLE makeup_styles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    style_name VARCHAR(100) NOT NULL,
    image_url VARCHAR(500)
);

-- 4. analysis_sessions
CREATE TABLE analysis_sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    face_shape ENUM('oval','round','square','oblong','heart'),
    face_point ENUM('upper','middle','lower','golden'),
    skin_tone ENUM('spring','summer','fall','winter'),
    skin_lab_b FLOAT,
    ratio_face_wh FLOAT,
    ratio_jaw_cheek FLOAT,
    ratio_forehead_cheek FLOAT,
    ratio_upper_third FLOAT,
    ratio_middle_third FLOAT,
    ratio_lower_third FLOAT,
    result JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 5. style_mapping_list
CREATE TABLE style_mapping_list (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    analysis_session_id BIGINT NOT NULL,
    type ENUM('hair','makeup','ootd') NOT NULL,
    hair_style_id BIGINT NULL,
    makeup_style_id BIGINT NULL,
    style_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (analysis_session_id) REFERENCES analysis_sessions(id),
    FOREIGN KEY (hair_style_id) REFERENCES hair_styles(id),
    FOREIGN KEY (makeup_style_id) REFERENCES makeup_styles(id)
);

-- 6. simulation_results
CREATE TABLE simulation_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    analysis_session_id BIGINT NOT NULL,
    hair_mapping_id BIGINT NULL,
    makeup_mapping_id BIGINT NULL,
    generated_image_path VARCHAR(500),
    is_saved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (analysis_session_id) REFERENCES analysis_sessions(id),
    FOREIGN KEY (hair_mapping_id) REFERENCES style_mapping_list(id),
    FOREIGN KEY (makeup_mapping_id) REFERENCES style_mapping_list(id)
);

-- 7. user_feedback
CREATE TABLE user_feedback (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    simulation_result_id BIGINT NOT NULL,
    target_type ENUM('hair','makeup') NOT NULL,
    feedback_text TEXT,
    applied_style_key VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (simulation_result_id) REFERENCES simulation_results(id)
);
```

---

## 관리자 계정

| 항목 | 값 |
|------|-----|
| nickname | admin |
| password | 1234 |
| role | admin |

---

## 참고

- 전체 프로젝트 문서: `C:\ai_exam\pj_styleflow\guidelines\styleflow.md`
- DB: 원격 MariaDB (host: 220.80.16.79, port: 3306, db: styleflowdb, user: styleflow)
