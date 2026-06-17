# pip → uv 전환 트러블슈팅

## 1. 프론트엔드 무한 새로고침

**증상**
`npm run dev` 실행 시 브라우저가 무한 새로고침되고, 터미널에 Turbopack FATAL 패닉이 반복 출력됨.

**원인**
Node.js v24와 Next.js 16의 Turbopack 사이에 버그가 있어 Turbopack이 주기적으로 패닉 → HMR 재연결 → 브라우저 새로고침이 반복됨.

**해결**
`frontend/package.json`의 dev 스크립트에 `--webpack` 플래그 추가.

```json
"scripts": {
  "dev": "next dev --webpack"
}
```

> `--webpack`은 Turbopack 대신 Webpack 번들러를 사용하며, Node.js 버전에 관계없이 동작함.

---

## 2. No module named 'tensorflow'

**증상**
`uv run python manage.py runserver` 실행 시 `ModuleNotFoundError: No module named 'tensorflow'` 발생.

**원인 1 — uv sync의 Windows tensorflow 처리 미흡**
Windows에서 `tensorflow`는 내부적으로 `tensorflow-intel`이라는 패키지로 설치됨. `uv sync`가 이 매핑을 제대로 처리하지 못해 설치를 건너뜀.

**원인 2 — pyproject.toml에 플랫폼 분기 없음**
`tensorflow==2.13.0`으로만 명시되어 있어 Windows에서 올바른 패키지를 찾지 못함.

**해결**
`pyproject.toml`에서 플랫폼별로 의존성을 분기.

```toml
# 변경 전
"tensorflow==2.13.0",

# 변경 후
"tensorflow==2.13.0; sys_platform != 'win32'",
"tensorflow-intel==2.13.0; sys_platform == 'win32'",
```

변경 후 lock 파일 재생성:
```
uv lock
uv sync
```

> 이후 `uv sync` 한 번으로 Windows/Mac/Linux 모두 자동 대응됨.

---

## 환경 셋업 가이드 (인수인계용)

### 사전 준비
- Python 3.11
- Node.js (v22 권장, v24는 Turbopack 버그 있음 — `--webpack`으로 우회 가능)
- uv (`pip install uv` 또는 공식 설치)

### 백엔드 환경 설치
```
uv venv --python 3.11
uv sync
```

VS Code 사용 시: `Ctrl+Shift+P` → Python 인터프리터 선택 → `.venv\Scripts\python.exe`

### 백엔드 실행
```
cd backend
.\run.bat
```

### 프론트엔드 실행
```
cd frontend
npm install
npm run dev
```

### 접속
http://localhost:3000/
