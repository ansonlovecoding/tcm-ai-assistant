# Tongue Coating Health Analysis

这套代码用于把 `shezhenv3-xml` 舌苔数据集训练成一个目标检测模型，并用检测到的舌象特征生成健康状态分析提示。

重要说明：模型输出只能作为学习、研究和健康风险提示，不能替代医生诊断。

## 1. 安装依赖

```powershell
pip install -r requirements.txt
```

## 2. 转换数据集

原始数据路径：

```text
D:\Study\DMU MSc\Block4 Applied AI&Research Method\Applied AI\mini project\Tongue coating\shezhen datasets\shezhenv3-xml\shezhenv3-xml
```

转换为 YOLO 格式：

```powershell
python scripts\prepare_yolo_dataset.py --source "D:\Study\DMU MSc\Block4 Applied AI&Research Method\Applied AI\mini project\Tongue coating\shezhen datasets\shezhenv3-xml\shezhenv3-xml" --output data\shezhen_yolo
```

只检查数据集、不生成训练文件：

```powershell
python scripts\prepare_yolo_dataset.py --source "D:\Study\DMU MSc\Block4 Applied AI&Research Method\Applied AI\mini project\Tongue coating\shezhen datasets\shezhenv3-xml\shezhenv3-xml" --output data\shezhen_yolo --dry-run
```

转换后会生成：

- `data\shezhen_yolo\dataset.yaml`
- `data\shezhen_yolo\labels\...`
- `data\shezhen_yolo\images\...`
- `data\shezhen_yolo\label_mapping.json`

## 3. 训练模型

```powershell
python train_yolo.py --data data\shezhen_yolo\dataset.yaml --epochs 80 --imgsz 640 --model yolo11n.pt
```

训练完成后，权重通常在：

```text
runs\tongue_coating\train\weights\best.pt
```

## 4. 舌苔健康分析

```powershell
python analyze_tongue_health.py --model runs\tongue_coating\train\weights\best.pt --image "D:\path\to\tongue.jpg" --mapping data\shezhen_yolo\label_mapping.json
```

如果你知道数字类别对应的真实舌象含义，可以复制并编辑：

```text
config\label_semantics.example.json
```

然后运行：

```powershell
python analyze_tongue_health.py --model runs\tongue_coating\train\weights\best.pt --image "D:\path\to\tongue.jpg" --mapping data\shezhen_yolo\label_mapping.json --semantics config\label_semantics.example.json
```

## 输出内容

分析脚本会输出：

- 检测到的舌象类别、置信度和区域大小
- 舌苔/异常区域占比
- 基于规则的健康风险提示
- 是否需要进一步人工检查

由于当前数据集 XML 中类别是数字标签，代码默认不会假装知道每个数字的医学含义。你可以在 `config\label_semantics.example.json` 中补充类别含义和风险规则，这样输出会更接近真实“舌苔分析健康状况”的应用。
