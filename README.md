# 🚧 AI 기반 도로 낙하물 탐지 및 모니터링 시스템

**YOLO11n · Transfer Learning · Flask · Raspberry Pi**

도로 영상에서 **wood(합판), box(박스), pet(페트병)** 낙하물을 탐지하고 탐지 결과를 웹 대시보드에서 확인할 수 있도록 구성한 AI 프로젝트입니다.

팀 프로젝트에서 수행한 모델 학습·비교와 시스템 구현 결과를 기반으로, 개인 포트폴리오에서는 **모델 선정 근거, 성능 비교, 오탐·미탐 분석, 웹/카메라 연동 과정**이 드러나도록 재구성했습니다.

## 🎯 프로젝트 목표

- 도로 낙하물 3종 wood / box / pet 탐지
- 동일 조건에서 YOLO11n 모델 성능 비교
- 사전학습 모델 Fine-tuning 및 EarlyStopping 기반 epoch 탐색
- Precision, Recall, mAP, FP/FN 및 confidence threshold 분석
- Flask 기반 탐지 대시보드 구현
- Raspberry Pi + USB 카메라 영상 입력 연동

## 🧠 모델 실험

최종 비교에서는 **팀 YOLO11n 88 epoch**와 **Alope 사전학습 기반 121 / 151 / 181 epoch 모델**을 동일한 평가 조건에서 비교했습니다.

| 항목 | 조건 |
|---|---|
| 클래스 | wood / box / pet |
| 평가 데이터 | test 371장 |
| Train/Val 중복 | 0장 |
| 이미지 크기 | 640 |
| 기본 Confidence | 0.25 |
| IoU | 0.5 |
| 지표 | Precision / Recall / mAP50 / mAP50-95 / FP / FN |

50/88/100 epoch처럼 임의 시점만 비교하는 문제를 줄이기 위해 EarlyStopping 기반 탐색을 추가했고, confidence 0.20~0.50 변화에 따른 오탐·미탐 trade-off도 분석했습니다.

## 🔬 프로젝트 진행 흐름

RetinaNet / YOLO11m 초기 비교 → 낙하물 3종 데이터 구성 → YOLO11n 학습 → Alope 사전학습 모델 Fine-tuning → EarlyStopping 탐색 → 팀 88ep vs Alope 121/151/181ep 비교 → Flask 대시보드 → Raspberry Pi 카메라 연동

## 💻 시스템 구성

Raspberry Pi + USB Camera → Frame Upload → AI Detection Server → Detection / Event History → Flask Dashboard

## 🖥️ 웹 대시보드

`dashboard/app.py`는 원격 AI 서버와 웹 UI 사이에서 카메라 스트림, 연결 상태, 탐지 이력, 이벤트 이미지·영상, 실시간 알림 및 AI 서버 상태를 연결합니다. 서버 주소는 `AI_SERVER_BASE` 환경변수로 변경할 수 있습니다.

## 📷 Raspberry Pi

- `camera_uploader.py` — USB 카메라 프레임 서버 전송
- `roi_config.py` — 카메라별 ROI 및 방향 기준 관리
- `roi_editor.py` — ROI 편집
- `traffic_roi_config.json` — ROI 설정값

## 🙋 담당 및 포트폴리오 개선

**모델 분석**
- YOLO 계열 모델의 동일 평가 데이터 기반 성능 비교
- Alope 사전학습 YOLO11n Fine-tuning 실험
- EarlyStopping 기반 epoch 탐색
- Precision / Recall / mAP 및 FP/FN 비교
- confidence threshold trade-off 분석
- 동일 영상 구간의 탐지 안정성 및 flicker 확인

**시스템 구현·검증**
- Flask 기반 교통 탐지 대시보드 구성 및 기능 개선
- 최근 탐지 결과와 전체 탐지 기록 UI 구성
- 카메라 상태 및 탐지 이벤트 연동 점검
- Raspberry Pi USB 카메라 연동 및 ROI 문제 분석

## 🧩 트러블슈팅

**학습 epoch 선정** — 임의 epoch 비교 대신 EarlyStopping을 적용해 validation 성능을 기준으로 후보 모델을 탐색했습니다.

**학습량과 실전 성능 차이** — loss만으로 모델을 선택하지 않고 test 데이터의 Precision, Recall, mAP, FP/FN 및 실제 영상 추론을 함께 확인했습니다.

**Confidence 병목** — threshold를 0.20~0.50으로 변경하여 FP 감소와 FN 증가 사이의 trade-off를 비교했습니다.

**ROI 적용 후 탐지 저하** — ROI 좌표, 입력 프레임 크기, 전처리 순서를 분리해 점검하고 ROI 설정을 별도 파일로 관리했습니다.

## 🛠️ Tech Stack

| 영역 | 기술 |
|---|---|
| AI / Vision | YOLO11n, Ultralytics, OpenCV |
| Evaluation | Precision, Recall, mAP50, mAP50-95, FP/FN |
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Edge | Raspberry Pi 4, USB Camera |
| Experiment | Google Colab, A100 GPU |
| Version Control | Git, GitHub |

## 📁 Repository Structure

```text
traffic-risk-monitoring-portfolio/
├── dashboard/       # Flask 대시보드
├── raspberrypi/     # 카메라 / ROI 코드
├── notebooks/       # 핵심 실험 노트북 (추가 예정)
├── results/         # 정량 평가 결과 (추가 예정)
├── docs/images/     # README 이미지 (추가 예정)
├── .gitignore
└── README.md
```

대용량 데이터셋, 모델 가중치, 원본 영상은 저장소에서 제외하고 재현에 필요한 코드와 대표 실험 결과를 중심으로 공개합니다.

## 🚀 실행

```powershell
cd dashboard
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:AI_SERVER_BASE="http://<AI_SERVER_IP>:5000"
python app.py
```

## 📌 포트폴리오 정리 상태

현재 Flask 대시보드 코드와 Raspberry Pi 연동 코드를 우선 공개했습니다. 다음 단계에서 핵심 Colab 노트북, 모델 비교 CSV/그래프, 대시보드 및 탐지 결과 화면을 선별해 추가합니다.
