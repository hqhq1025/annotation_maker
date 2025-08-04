# 视频拼接训练数据生成器

该工具用于将视频拼接计划、原始视频标注和分布式图像帧合并为训练用对话格式JSON文件，用于流视频场景切换训练。

## 功能特点

1. **多源数据整合**：
   - 拼接策略文件 (concat_metadata.json)
   - 原始视频标注文件 (concatenated_video_annotations.json)
   - 分布式图像帧目录 (sample_frames/)

2. **正确的对话流格式**：
   - 每个图像帧后都有对应的模型响应
   - 大多数情况下输出`<|silent|>`
   - 仅在视频片段的最后一帧输出`<|response|> [summary]`
   - 最后以`<|END_OF_STREAMING|>`结束

3. **精确的时间处理**：
   - 使用`floor(t)`处理时间戳
   - 每个原始视频的帧从0开始编号
   - 准确识别视频片段切换点

## 输入文件

### 1. 拼接策略文件 (concat_metadata.json)

```json
[
  {
    "concat_video": "concat_00000.mp4",
    "total_duration": 110.65561166920506,
    "boundaries": [
      {
        "video_id": "video_6183",
        "start_time": 0.0,
        "end_time": 26.49646713771497
      },
      {
        "video_id": "video_7678",
        "start_time": 26.49646713771497,
        "end_time": 54.88343509005948
      }
    ]
  }
]
```

### 2. 原始视频标注文件 (concatenated_video_annotations.json)

```json
[
  {
    "video": "concat_00000",
    "data": [
      {
        "video_id": "video_6183",
        "start": 0.0,
        "end": 26.49646713771497,
        "summary": "A video depicts a sequence where various objects are arranged on a white surface..."
      }
    ]
  }
]
```

### 3. 图像帧路径

结构：
```
/path/to/sample_frames/
  ├── video_6183/
  │   ├── frame_00000.jpg
  │   ├── frame_00001.jpg
  │   └── ...
  ├── video_7678/
  │   ├── frame_00000.jpg
  │   └── ...
  └── ...
```

## 输出格式

生成的训练数据文件 (train_conversations.json) 格式如下：

```json
[
  {
    "video": "concat_00000.mp4",
    "images": [
      "video_6183/frame_00000.jpg",
      "video_6183/frame_00001.jpg",
      "video_7678/frame_00000.jpg",
      ...
    ],
    "conversations": [
      {
        "from": "human",
        "value": "请适当地描述一下视频中发生的内容"
      },
      {
        "from": "human",
        "value": "<image>"
      },
      {
        "from": "gpt",
        "value": "<|silent|>"
      },
      ...
      {
        "from": "gpt",
        "value": "<|response|> [summary text]"
      },
      ...
      {
        "from": "human",
        "value": "<image>"
      },
      {
        "from": "human",
        "value": "<|END_OF_STREAMING|>"
      },
      {
        "from": "gpt",
        "value": "<|response|> [last summary text]"
      }
    ]
  }
]
```

## 使用方法

### 命令行参数

```bash
python generate_train_conversations.py \
  --concat_plan /path/to/concat_metadata.json \
  --annotations /path/to/concatenated_video_annotations.json \
  --sample_frames_dir /path/to/sample_frames \
  --output /path/to/train_conversations.json
```

### 默认路径

如果不指定参数，脚本将使用以下默认路径：
- 拼接计划文件: `/data1/whq/annotation_maker/concat_planer/concat_metadata.json`
- 原始视频标注文件: `/data1/whq/annotation_maker/annotation_concatter/concatenated_video_annotations.json`
- 图像帧根目录: `/data1/whq/sample_frames`
- 输出文件: `/data1/whq/annotation_maker/annotation_concatter/train_conversations.json`

## 运行示例

```bash
cd /data1/whq/annotation_maker/annotation_concatter
python generate_train_conversations.py
```

## 清理空Summary

有些原始数据集中的视频片段可能没有标注，因此它们的summary字段为空。我们提供了一个清理程序来移除这些包含空summary的拼接视频：

```bash
python clean_empty_summaries.py \
  --input /path/to/concatenated_video_annotations.json \
  --output /path/to/concatenated_video_annotations_cleaned.json
```

清理程序会：
1. 检查每个拼接视频是否包含空summary的片段
2. 如果一个拼接视频包含任何空summary的片段，则移除整个拼接视频
3. 输出清理统计信息

默认情况下，清理程序会处理默认路径下的文件并生成清理后的版本。

## 输出说明

生成的[train_conversations.json](file:///data1/whq/annotation_maker/annotation_concatter/train_conversations.json)文件将包含以下内容：
- 每个拼接视频对应一个对象
- 图像路径使用相对路径格式
- 对话格式严格按照要求构造
- 只在视频片段结束时输出summary