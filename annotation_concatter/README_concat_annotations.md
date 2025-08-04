# 视频拼接标注数据构造系统

## 功能特点

本系统旨在基于现有的视频拼接策略与原始标注，构造拼接后视频的完整语义标注数据，并借助大语言模型（LLM）自动生成衔接连贯的自然语言描述段落。

## 输入数据说明

### 1. 视频帧图像目录（采样结果）

所有原始视频已按 1 秒 1 帧采样。每个视频存放在以视频名命名的文件夹中。

### 2. 原始视频标注（自然语言段落描述）

每个原始视频的标注为自然语言段落形式，存储在 `sharegpt4o/video_conversations/gpt4o.jsonl` 文件中。

### 3. 拼接策略文件（拼接信息）

描述每个新拼接视频是由哪些原视频组合而成，存储在 `concat_plan/concat_metadata.json` 文件中。

## 安装依赖

```bash
# 该脚本只使用Python标准库，无需额外安装依赖
python3 generate_concat_annotations.py
```

## 使用方法

```bash
python3 generate_concat_annotations.py
```

## 输出数据格式

输出为一个 JSON 文件，每个拼接视频一个 JSON 对象：

```json
[
  {
    "video": "concat_00000",
    "data": [
      {
        "start": 0.0,
        "end": 26.49,
        "summary": "This video begins with a man arranging vegetables..."
      },
      {
        "start": 26.49,
        "end": 54.88,
        "summary": "The scene then transitions to a kitchen where a woman prepares a dish..."
      }
    ]
  }
]
```

## 核心处理流程

1. 加载拼接策略 JSON 文件
2. 整理帧图像路径
3. 加载原始标注（GPT描述）
4. 构造 Prompt 并调用大模型（如 GPT）
5. 构造最终标注 JSON

## 可选增强项

- 将每段标注中涉及的帧图像路径记录下来（便于训练用图文对）
- 保存调用大模型的 prompt 和 response，用于审核/复用
- 添加 log 输出，跟踪处理进度

## 开发提醒

- 不要读取视频原文件，只使用采样后的帧图像和视频元数据
- 每帧间隔为 1 秒，帧名推断时间戳
- 拼接策略中时间戳为浮点数，请用 `int(x)` 取帧 index
- 为所有变量加上清晰注释，结构化代码，便于维护

## 注意事项

当前版本为演示版本，实际使用时需要集成真实的LLM API调用。在 [process_concat_video](file:///data1/whq/generate_concat_annotations.py#L128-L166) 函数中，标注了需要调用LLM的位置，用户可以根据自己的需求替换为实际的API调用代码。