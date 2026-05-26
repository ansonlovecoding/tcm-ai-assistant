# Tongue Coating Health Analysis · 舌苔健康分析

> Train a YOLO object-detection model on the **shezhenv3-coco** tongue
> dataset, then use the detected tongue-image features to surface
> rule-based health-risk hints.
>
> 用 **shezhenv3-coco** 舌苔数据集训练目标检测模型，再以检测到的舌象特征
> 生成基于规则的健康提示。

**Languages:** [English](#english) · [中文](#中文)

> ⚠ **Disclaimer.** Model output is for learning / research / health-risk
> hinting only. It does **not** constitute a medical diagnosis. Always
> consult a licensed TCM practitioner.
>
> ⚠ **免责声明。** 模型输出仅用于学习、研究及健康风险提示，**不构成**
> 医学诊断。如有健康问题请咨询执业中医师。

---

## English

### What's in this folder

```
tongue-analysis/
├── coco/
│   ├── shezhenv3_coco_dataset.yaml   # YOLO dataset descriptor
│   ├── tongue_label_profiles.json    # rules linking labels → health hints
│   ├── predict_tongue_disease.py     # single-image CLI inference
│   └── tongue_disease_api.py         # FastAPI wrapper around the predictor
├── datasets/
│   └── shezhenv3-coco/               # downloaded dataset (see step 2)
├── TESTDATA/                          # sample tongue images for sanity checks
├── runs/                              # YOLO training outputs (weights, logs)
├── weights/                           # frozen / shipped weights
├── train_yolo.py                      # YOLO training entry point
├── predict_result_from_bytes.py       # in-process helper: bytes → JSON result
├── requirements.txt
└── yolo11n.pt                         # YOLOv11-nano starting checkpoint
```

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` pulls in `ultralytics`, `opencv-python`, `Pillow`,
`PyYAML`, and `numpy`. A CUDA-capable GPU is recommended for training but
not required for inference.

### 2. Prepare the dataset

Download the **shezhenv3** tongue dataset from Dryad and unzip it under
`tongue-analysis/datasets/` so the layout looks like the table below.

| Item                | Location                                                                |
|---------------------|-------------------------------------------------------------------------|
| Dataset (download)  | <https://datadryad.org/dataset/doi:10.5061/dryad.1c59zw48r>             |
| Dataset (local)     | `tongue-analysis/datasets/shezhenv3-coco`                               |
| YOLO YAML           | `tongue-analysis/coco/shezhenv3_coco_dataset.yaml`                      |
| Label → profile map | `tongue-analysis/coco/tongue_label_profiles.json`                       |

### 3. Train the model

Verify the GPU is visible:

```bash
nvidia-smi
```

Train (bash on macOS/Linux):

```bash
cd tongue-analysis

python train_yolo.py \
  --data ./coco/shezhenv3_coco_dataset.yaml \
  --epochs 80 \
  --imgsz 640 \
  --batch 4 \
  --model yolo11n.pt \
  --device 0 \
  --project runs/shezhenv3_coco \
  --name train
```

Equivalent on PowerShell (Windows) — same flags, backtick line continuation:

```powershell
cd tongue-analysis

python .\train_yolo.py `
  --data .\coco\shezhenv3_coco_dataset.yaml `
  --epochs 80 `
  --imgsz 640 `
  --batch 4 `
  --model yolo11n.pt `
  --device 0 `
  --project runs\shezhenv3_coco `
  --name train
```

The best weights are written to:

```
tongue-analysis/runs/train-2/weights/best.pt
```

### 4. Inference

#### CLI — analyse one image

```bash
python coco/predict_tongue_disease.py \
  --model ./runs/train-2/weights/best.pt \
  --image ./TESTDATA/TESTDATA3.jpg \
  --save-json  ./runs/shezhenv3_coco/predict_result.json \
  --save-image ./runs/shezhenv3_coco/predict_result.jpg
```

#### REST API — Swagger-driven testing

```bash
cd tongue-analysis/coco
python -m uvicorn tongue_disease_api:app --host 127.0.0.1 --port 8000
```

Then open <http://127.0.0.1:8000/docs> for Swagger UI.

#### Programmatic — in-process helper

`tongue-analysis/predict_result_from_bytes.py` exposes a function suitable
for embedding in another service (the FastAPI backend, an agent, etc.).

| Input  | `bytes` — raw image content (JPG / PNG)             |
|--------|-----------------------------------------------------|
| Output | JSON string describing the predicted labels & hints |

### 5. Output

The predictor emits:

- detected tongue-image classes, with confidence and region size
- coating / abnormal-area ratio
- rule-based health-risk hints
- a flag for whether human review is recommended

JSON results land at:

```
tongue-analysis/runs/shezhenv3_coco/predict_result.json
```

---

## 中文

### 目录结构

```
tongue-analysis/
├── coco/
│   ├── shezhenv3_coco_dataset.yaml   # YOLO 数据集配置
│   ├── tongue_label_profiles.json    # 类别 → 健康提示映射
│   ├── predict_tongue_disease.py     # 单图推理 CLI
│   └── tongue_disease_api.py         # FastAPI 接口封装
├── datasets/
│   └── shezhenv3-coco/               # 下载后的数据集（见第 2 步）
├── TESTDATA/                          # 调试用样张
├── runs/                              # YOLO 训练输出（权重、日志）
├── weights/                           # 固化 / 发布权重
├── train_yolo.py                      # YOLO 训练入口
├── predict_result_from_bytes.py       # 进程内调用：bytes → JSON 字符串
├── requirements.txt
└── yolo11n.pt                         # YOLOv11-nano 预训练权重
```

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：`ultralytics`、`opencv-python`、`Pillow`、`PyYAML`、`numpy`。
训练建议使用带 CUDA 的 GPU；仅推理时 CPU 即可。

### 2. 准备数据集

从 Dryad 下载 **shezhenv3** 舌苔数据集，并解压到
`tongue-analysis/datasets/`，按下表组织好目录结构。

| 项目             | 路径                                                                 |
|------------------|----------------------------------------------------------------------|
| 数据集下载       | <https://datadryad.org/dataset/doi:10.5061/dryad.1c59zw48r>          |
| 数据集放置位置   | `tongue-analysis/datasets/shezhenv3-coco`                            |
| YOLO YAML        | `tongue-analysis/coco/shezhenv3_coco_dataset.yaml`                   |
| 类别 → 提示映射  | `tongue-analysis/coco/tongue_label_profiles.json`                    |

### 3. 训练模型

先确认 GPU 是否可用：

```bash
nvidia-smi
```

bash（macOS / Linux）：

```bash
cd tongue-analysis

python train_yolo.py \
  --data ./coco/shezhenv3_coco_dataset.yaml \
  --epochs 80 \
  --imgsz 640 \
  --batch 4 \
  --model yolo11n.pt \
  --device 0 \
  --project runs/shezhenv3_coco \
  --name train
```

PowerShell（Windows）：

```powershell
cd tongue-analysis

python .\train_yolo.py `
  --data .\coco\shezhenv3_coco_dataset.yaml `
  --epochs 80 `
  --imgsz 640 `
  --batch 4 `
  --model yolo11n.pt `
  --device 0 `
  --project runs\shezhenv3_coco `
  --name train
```

训练完成后，最佳权重路径：

```
tongue-analysis/runs/train-2/weights/best.pt
```

### 4. 推理

#### CLI — 单张推理

```bash
python coco/predict_tongue_disease.py \
  --model ./runs/train-2/weights/best.pt \
  --image ./TESTDATA/TESTDATA3.jpg \
  --save-json  ./runs/shezhenv3_coco/predict_result.json \
  --save-image ./runs/shezhenv3_coco/predict_result.jpg
```

#### REST API — Swagger 测试

```bash
cd tongue-analysis/coco
python -m uvicorn tongue_disease_api:app --host 127.0.0.1 --port 8000
```

之后访问 <http://127.0.0.1:8000/docs> 即可使用 Swagger UI 调试。

#### 进程内调用

`tongue-analysis/predict_result_from_bytes.py` 提供一个可直接被其他
Python 服务调用的封装函数（适合接入 FastAPI 后端或 AI Agent）。

| 输入 | `bytes` — 原始图片内容（JPG / PNG）           |
|------|-----------------------------------------------|
| 输出 | JSON 字符串，包含识别结果与健康提示           |

### 5. 输出

分析脚本输出：

- 检测到的舌象类别，含置信度与区域面积
- 舌苔 / 异常区域占比
- 基于规则的健康风险提示
- 是否建议进一步人工检查

JSON 结果保存在：

```
tongue-analysis/runs/shezhenv3_coco/predict_result.json
```
