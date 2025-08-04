# Annotation Maker Toolkit

视频标注生成工具集，用于生成视频理解任务所需的训练数据。该工具集包含多个子模块，用于处理视频采样、拼接策略生成、标注数据构造和对话格式转换等任务。

## 目录结构

```
annotation_maker/
├── video_sampler/          # 视频帧采样器
├── concat_planer/          # 视频拼接策略生成器
├── annotation_concatter/   # 拼接视频标注构造器
├── data_filter/            # 数据清理和过滤工具
├── conversation_maker/     # 对话格式生成器
├── statistic/              # 数据统计分析工具
├── generate_pipeline_script.py     # 命令行式流程脚本生成器
└── interactive_pipeline_generator.py  # 交互式流程脚本生成器
```

## 模块功能介绍

### 1. video_sampler - 视频帧采样器

从视频文件中按固定时间间隔采样帧图像，并生成元数据文件。

**主要功能：**
- 以指定时间间隔（默认1秒）从视频中采样帧
- 生成包含视频信息和帧路径的元数据文件
- 支持并行处理，提高处理效率
- 自动跳过损坏或过短的视频文件

**输出格式：**
```
sample_frames/
├── video_001/
│   ├── frame_00000.jpg
│   ├── frame_00001.jpg
│   └── ...
├── video_002/
│   ├── frame_00000.jpg
│   └── ...
└── video_metadata.json
```

### 2. concat_planer - 视频拼接策略生成器

根据视频元数据生成拼接策略，将多个短视频组合成较长的视频序列。

**主要功能：**
- 灵活控制拼接视频的数量和时长范围
- 支持视频复用策略（均衡使用或随机选择）
- 保证每个视频在拼接中保持完整
- 生成详细的拼接元数据记录

**输出格式：**
```json
[
  {
    "concat_video": "concat_00000.mp4",
    "total_duration": 110.66,
    "boundaries": [
      {
        "video_id": "video_6183",
        "start_time": 0.0,
        "end_time": 26.50
      }
    ],
    "videos": ["video_6183", "video_7678"]
  }
]
```

### 3. annotation_concatter - 拼接视频标注构造器

基于拼接策略和原始视频标注，构造拼接后视频的完整语义标注数据。

**主要功能：**
- 整合拼接策略与原始标注数据
- 生成衔接连贯的自然语言描述段落
- 支持调用大语言模型生成过渡描述

**输出格式：**
```json
[
  {
    "video": "concat_00000",
    "data": [
      {
        "start": 0.0,
        "end": 26.49,
        "summary": "This video begins with a man arranging vegetables..."
      }
    ]
  }
]
```

### 4. data_filter - 数据清理和过滤工具

清理和过滤标注数据，确保训练数据质量。

**主要功能：**
- 移除包含空summary的拼接视频
- 输出清理统计信息
- 生成清理后的标注文件

### 5. conversation_maker - 对话格式生成器

将拼接视频标注转换为训练用对话格式。

**主要功能：**
- 生成符合流式视频理解任务要求的对话格式
- 正确处理视频片段切换点
- 仅在视频片段结束时输出summary

**输出格式：**
```json
[
  {
    "video": "concat_00000.mp4",
    "images": [
      "video_6183/frame_00000.jpg",
      "video_6183/frame_00001.jpg"
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
      }
    ]
  }
]
```

### 6. statistic - 数据统计分析工具

分析拼接视频数据，生成统计报告。

**主要功能：**
- 统计拼接视频时长分布
- 分析元视频数量分布
- 提供详细的数据分布信息

## 自动化流程脚本生成器

为了避免手动执行每个步骤，我们提供了两种自动化脚本生成器：

### 1. 命令行式脚本生成器 (generate_pipeline_script.py)

通过命令行参数指定所有配置项。

#### 使用方法

```bash
cd /data1/whq/annotation_maker
python3 generate_pipeline_script.py \\
  --input_videos_dir /path/to/your/videos \\
  --sample_frames_dir /path/to/sample_frames \\
  [--其他可选参数]
```

这将生成一个名为 `run_annotation_pipeline.sh` 的脚本，执行该脚本即可按顺序完成所有步骤。

#### 可配置参数

- `--workspace_root`: 工作区根目录 (默认: /data1/whq)
- `--input_videos_dir`: 输入视频目录 (必需)
- `--sample_frames_dir`: 采样帧输出目录 (默认: /data1/whq/sample_frames)
- `--output_script`: 生成的脚本文件名 (默认: run_annotation_pipeline.sh)

视频采样相关参数:
- `--sampling_interval`: 采样间隔(秒) (默认: 1.0)
- `--min_video_duration`: 最小视频时长(秒) (默认: 2.0)
- `--num_workers`: 并行处理进程数 (默认: 8)

视频拼接相关参数:
- `--total_concats`: 生成的拼接视频总数 (默认: 500)
- `--min_videos_per_concat`: 每个拼接视频最少包含的视频数量 (默认: 2)
- `--max_videos_per_concat`: 每个拼接视频最多包含的视频数量 (默认: 6)
- `--target_duration_min`: 拼接视频的最小目标时长(秒) (默认: 20.0)
- `--target_duration_max`: 拼接视频的最大目标时长(秒) (默认: 60.0)
- `--reuse_mode`: 视频复用策略 ("balanced" 或 "random") (默认: balanced)
- `--max_usage_ratio`: 视频使用比例上限 (默认: 2.0)

### 2. 交互式脚本生成器 (interactive_pipeline_generator.py)

通过问答方式逐步输入参数，更适合不想一次性输入所有参数的用户。

#### 使用方法

```bash
cd /data1/whq/annotation_maker
python3 interactive_pipeline_generator.py
```

按照提示逐步输入各项参数，程序会自动生成执行脚本。

## 使用流程

1. **视频帧采样** - 使用 `video_sampler` 对原始视频进行采样
2. **生成拼接策略** - 使用 `concat_planer` 生成视频拼接计划
3. **构造标注数据** - 使用 `annotation_concatter` 构造拼接视频标注
4. **数据清理** - 使用 `data_filter` 清理无效数据
5. **生成对话格式** - 使用 `conversation_maker` 生成训练用对话数据
6. **数据分析** - 使用 `statistic` 分析生成的数据集

或者使用自动化方式：
1. **生成执行脚本** - 使用 `generate_pipeline_script.py` 或 `interactive_pipeline_generator.py` 生成执行脚本
2. **执行流程** - 运行生成的脚本完成所有步骤

## 依赖关系

大部分工具只使用Python标准库，部分工具需要安装额外依赖：

```bash
pip install opencv-python tqdm numpy
```

## 许可证

MIT