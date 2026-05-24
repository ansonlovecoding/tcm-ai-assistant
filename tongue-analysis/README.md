# Tongue Coating Health Analysis

这套代码用于把 `shezhenv3-coco` 舌苔数据集训练成一个目标检测模型，并用检测到的舌象特征生成健康状态分析提示。

重要说明：模型输出只能作为学习、研究和健康风险提示，不能替代医生诊断。

## 1. 安装依赖

```powershell
pip install -r requirements.txt
```

## 2. 转换数据集

原始数据路径：

```text
D:\Study\DMU MSc\Block4 Applied AI&Research Method\Applied AI\mini project\Tongue coating\shezhen datasets\shezhenv3-coco\shezhenv3-coco
```

下载链接：
```text
https://datadryad.org/dataset/doi:10.5061/dryad.1c59zw48r
```

YOLO数据集yaml文件：

```text
D:\Study\DMU MSc\Block4 Applied AI&Research Method\Applied AI\mini project\tcm-ai-assistant\tongue-analysis\coco\shezhenv3_coco_dataset.yaml
```

舌纹病症配置文件：

```text
D:\Study\DMU MSc\Block4 Applied AI&Research Method\Applied AI\mini project\tcm-ai-assistant\tongue-analysis\coco\tongue_label_profiles.json
```

## 3. 训练模型

```powershell
D:\Study\DMU MSc\Block4 Applied AI&Research Method\Applied AI\mini project\tcm-ai-assistant\tongue-analysis
$env:YOLO_CONFIG_DIR="D:\Study\DMU MSc\Block4 Applied AI&Research Method\Applied AI\mini project\tcm-ai-assistant\tongue-analysis\ultralytics_config"

E:\Software\python310\python.exe train_yolo.py `
  --data "D:\Study\DMU MSc\Block4 Applied AI&Research Method\Applied AI\mini project\tcm-ai-assistant\tongue-analysis\coco\shezhenv3_coco_dataset.yaml" `
  --epochs 80 `
  --imgsz 640 `
  --batch 4 `
  --model yolo11n.pt `
  --device 0 `
  --project runs\shezhenv3_coco `
  --name train
  
  检查是否使用GPU：
  nvidia-smi
```

训练完成后，权重通常在：

```text
runs\runs\train-2\weights\best.pt
```

## 4. 舌苔健康分析

```powershell
E:\Software\python310\python.exe "D:\Study\DMU MSc\Block4 Applied AI&Research Method\Applied AI\mini project\tcm-ai-assistant\tongue-analysis\coco\predict_tongue_disease.py" `
  --model "D:\Study\DMU MSc\Block4 Applied AI&Research Method\Applied AI\mini project\tcm-ai-assistant\tongue-analysis\runs\train-2\weights\best.pt" `
  --image "D:\Study\DMU MSc\Block4 Applied AI&Research Method\Applied AI\mini project\tcm-ai-assistant\tongue-analysis\TESTDATA\TESTDATA3.jpg" `
  --save-json "D:\Study\DMU MSc\Block4 Applied AI&Research Method\Applied AI\mini project\tcm-ai-assistant\tongue-analysis\runs\shezhenv3_coco\predict_result.json" `
  --save-image "D:\Study\DMU MSc\Block4 Applied AI&Research Method\Applied AI\mini project\tcm-ai-assistant\tongue-analysis\runs\shezhenv3_coco\predict_result.jpg"
```

也可以通过运行API形势进行测试：
```text
启动API：
cd dataset-d-study-dmu-msc-block4\coco
python -m uvicorn tongue_disease_api:app --host 127.0.0.1 --port 8000

http://127.0.0.1:8000/docs
```

## 输出内容

分析脚本会输出：

- 检测到的舌象类别、置信度和区域大小
- 舌苔/异常区域占比
- 基于规则的健康风险提示
- 是否需要进一步人工检查
- 输出分析内容位置在
```text
D:\Study\DMU MSc\Block4 Applied AI&Research Method\Applied AI\mini project\tcm-ai-assistant\tongue-analysis\runs\shezhenv3_coco\predict_result.json
```
## 函数包装

输入：图片的bytes值
输出：返回识别结果的json文件，文件名：predict_result.json，路径：\tongue-analysis根目录下

