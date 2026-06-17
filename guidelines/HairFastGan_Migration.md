# HairFastGAN CPU→GPU 마이그레이션 메모

## 배경
로컬 환경(CPU only, torch 1.13.1+cpu)에서 동작하도록 패치한 내용 기록.
원격 서버(RTX 2080Ti)로 이전 시 확인 필요.

---

## 수정한 파일 목록

### 자동 감지 방식으로 수정 (CUDA 있으면 GPU, 없으면 CPU 자동)
별도 복구 불필요. 서버에서 CUDA가 잡히면 자동으로 GPU로 동작.

| 파일 | 수정 내용 |
|------|-----------|
| `hair_swap.py` | `--device` 기본값 `'cuda'` → `torch.cuda.is_available()` 자동감지 |
| `models/stylegan2/op/fused_act.py` | CUDA 컴파일 `torch.cuda.is_available()` 조건부 처리 |
| `models/stylegan2/op/upfirdn2d.py` | 동일 |
| `models/FeatureStyleEncoder/pixel2style2pixel/models/stylegan2/op/fused_act.py` | 동일 |
| `models/FeatureStyleEncoder/pixel2style2pixel/models/stylegan2/op/upfirdn2d.py` | 동일 |
| `models/Encoders.py` | `clip.load` device 자동감지, `latent_avg` map_location `'cpu'` 고정 |
| `models/CtrlHair/external_code/face_parsing/my_parsing_util.py` | `.cuda()` 조건부 처리 |
| `models/sean_codes/models/pix2pix_model.py` | style code `.cuda()` 조건부 처리 |
| `models/sean_codes/models/networks/normalization.py` | `device='cuda'` → `device=x.device` |
| `utils/bicubic.py` | cuda 기본값 `True` → `torch.cuda.is_available()` 자동감지 |
| `main.py` | `torch.load` 전역 패치 (map_location 없을 시 cpu로 로드) |

---

### GPU 서버 이전 시 반드시 수동으로 되돌려야 할 파일

| 파일 | 수정 내용 | 복구 방법 |
|------|-----------|-----------|
| `models/FeatureStyleEncoder/configs/001.yaml` | `device: 'cuda'` → `'cpu'` | `'cpu'` → `'cuda'` 로 변경 |
| `models/sean_codes/models/pix2pix_model.py` | `gpu_ids=[0]` → `gpu_ids=[]` | `[]` → `[0]` 으로 변경 |

---

## 서버 이전 체크리스트

- [ ] CUDA 버전 확인 (`nvidia-smi`)
- [ ] torch CUDA 버전 맞춰 재설치 (`torch==1.13.1+cu117` 등)
- [ ] `001.yaml` device `'cpu'` → `'cuda'` 복구
- [ ] `pix2pix_model.py` `gpu_ids=[]` → `[0]` 복구
- [ ] `torch.cuda.is_available()` 확인 후 실행 테스트

---

## 참고: pretrained_models 구조

HuggingFace에서 다운로드 후 아래 경로에 위치해야 함.
`model_downloader.py`는 `HairFastGan_test/` 디렉토리 안에서 실행할 것.

```
HairFastGan_test/pretrained_models/
├── ArcFace/
├── BiSeNet/
├── Blending/
├── encoder4editing/
├── FeatureStyleEncoder/
├── PostProcess/
├── Rotate/
├── sean_checkpoints/
├── ShapeAdaptor/
├── STAR/
└── StyleGAN/
```
