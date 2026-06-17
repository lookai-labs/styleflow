# BeautyGAN 사용법

## 1. 파일별 역할

### test.py
커맨드라인에서 **단일 이미지에 메이크업을 적용**하는 스크립트.  
소스 이미지(민낯)와 레퍼런스 이미지(메이크업)를 입력받아 메이크업이 적용된 결과 이미지를 저장한다.

### get_samples.py
미리 정의된 여러 이미지 쌍에 대해 **일괄 처리(배치)**하는 스크립트.  
여성(F1~F3 × FS1~FS3)과 남성(M1~M3 × MS1~MS3) 조합 총 18장을 처리해  
`소스 / 레퍼런스 / 결과` 3단 비교 이미지를 `samples/` 폴더에 저장한다.

### test.ipynb
BeautyGAN의 전체 동작 과정을 **단계별로 시각화**하는 Jupyter 노트북.  
얼굴 탐지 → 랜드마크 검출 → 얼굴 정렬 → 모델 추론 순서로 각 단계의 결과를  
이미지로 확인할 수 있어 학습·실험 목적에 적합하다.

---

## 2. 사용법

### 환경 요구사항

#### Python 3.11 환경 (현재 권장)

| 패키지 | 버전 |
|--------|------|
| Python | 3.11.15 (Anaconda) |
| tensorflow | 2.13.0 |
| dlib | 19.24.2 |
| numpy | 1.24.3 |
| Pillow | 12.2.0 |
| matplotlib | 3.10.9 |
| imageio | 2.37.3 |
| opencv-python | 4.8.1.78 |

> TF1 모델 파일(.meta, .index, .data)은 `tf.compat.v1` 모드로 그대로 로드됩니다.

**가상환경 생성**
```
conda create -n p311_beauty python=3.11
conda activate p311_beauty
```

**패키지 설치**
```bash
pip install tensorflow==2.13.0 dlib numpy Pillow matplotlib imageio opencv-python
```

---

#### Python 3.6 환경 (구버전, 참고용)

| 패키지 | 버전 |
|--------|------|
| Python | 3.6.13 (Anaconda) |
| tensorflow | 1.9.0 |
| dlib | 19.22.0 |
| numpy | 1.19.5 |
| Pillow | 8.4.0 |
| matplotlib | 3.3.4 |
| imageio | 2.15.0 |

**가상환경 생성**
```
conda create -n p36t19_beauty python=3.6
```

**패키지 설치**
```bash
pip install tensorflow==1.9.0 dlib==19.22.0 numpy==1.19.5 Pillow==8.4.0 matplotlib==3.3.4 imageio==2.15.0
```

---

### test.py

**기본 실행** (기본값: `imgs/no_makeup/M1.png` → `imgs/makeup/XMY-136.png`)
```bash
python test.py
```

**옵션 지정 실행**
```bash
python test.py --source <민낯_이미지_경로> --reference <메이크업_이미지_경로> --output <저장_경로>
```

**예시**
```bash
python test.py --source imgs/no_makeup/F1.png --reference imgs/makeup/FS2.png --output result.png
```

| 인수 | 기본값 | 설명 |
|------|--------|------|
| `--source` | `imgs/no_makeup/M1.png` | 메이크업을 적용할 원본(민낯) 이미지 경로 |
| `--reference` | `imgs/makeup/XMY-136.png` | 스타일을 참조할 메이크업 이미지 경로 |
| `--output` | `output.png` | 결과 이미지 저장 경로 |

---

### get_samples.py

**실행** (인수 없음, 경로는 스크립트 내 `PAIRS` 변수에 고정)
```bash
python get_samples.py
```

- 결과 이미지는 `samples/` 폴더에 `{소스명}_{레퍼런스명}.png` 형식으로 저장된다.  
  예: `F1_FS2.png`
- 처리 대상 이미지를 변경하려면 스크립트 상단의 `PAIRS` 변수를 수정한다.

```python
PAIRS = [
    {
        'sources':    ['F1', 'F2', 'F3'],      # imgs/no_makeup/ 아래 파일명
        'references': ['FS1', 'FS2', 'FS3'],   # imgs/makeup/ 아래 파일명
    },
    ...
]
```

---

## 3. 동작 원리

BeautyGAN은 GAN(Generative Adversarial Network) 기반의 **인스턴스 레벨 메이크업 전이** 모델이다.

```
소스 이미지 (민낯)           레퍼런스 이미지 (메이크업)
      │                              │
      ▼                              ▼
 얼굴 탐지 (dlib)            얼굴 탐지 (dlib)
      │                              │
      ▼                              ▼
 5점 랜드마크 검출            5점 랜드마크 검출
      │                              │
      ▼                              ▼
 얼굴 정렬 (256×256)          얼굴 정렬 (256×256)
      │                              │
      └──────────┬───────────────────┘
                 ▼
        BeautyGAN Generator
          (TensorFlow 모델)
                 │
                 ▼
         결과 이미지 출력
     (소스 얼굴 + 레퍼런스 메이크업)
```

**핵심 처리 단계:**

1. **얼굴 탐지**: dlib의 정면 얼굴 탐지기로 이미지에서 얼굴 영역을 찾는다.
2. **랜드마크 검출**: 5점 얼굴 랜드마크 모델(`shape_predictor_5_face_landmarks.dat`)로 눈·코·입 위치를 파악한다.
3. **얼굴 정렬**: 랜드마크 기준으로 얼굴을 정규화해 256×256 크기로 맞춘다.
4. **전처리**: 픽셀값을 `[0,255]`에서 `[-1,1]` 범위로 정규화한다.
5. **GAN 추론**: Generator가 소스 얼굴(`X`)과 레퍼런스 얼굴(`Y`)을 입력받아, 소스의 얼굴 구조는 유지하면서 레퍼런스의 메이크업 스타일(색상, 질감)만 전이한 결과(`Xs`)를 생성한다.
6. **후처리**: 출력값을 `[-1,1]`에서 `[0,255]`로 역변환해 이미지로 저장한다.
