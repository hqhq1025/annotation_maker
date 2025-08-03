# 视频拼接策略程序

该程序用于将多个短视频拼接成较长的视频单元，主要用于构造训练/评测用的拼接视频集。

## 功能特点

1. **灵活拼接控制**：
   - 可自定义每个拼接视频包含的视频数量范围
   - 控制拼接视频的总时长范围
   - 保证每个视频在拼接中保持完整，不会被截断

2. **智能视频复用策略**：
   - 支持是否允许视频复用
   - 提供两种复用模式："balanced"（均衡使用）和"random"（随机选择）
   - 限制单个视频的最大使用次数，避免某些视频被过度使用

3. **完整的元数据记录**：
   - 生成详细的拼接记录，包括每个拼接视频的组成
   - 输出为JSON格式，便于后续处理

## 安装依赖

程序使用Python标准库编写，无需额外安装依赖：

```bash
python3 concat_planer.py --help
```

## 使用方法

### 命令行参数

```bash
python3 concat_planer.py \
  --video_metadata /data1/whq/sample_videos/video_metadata.json \
  --output_dir /data1/whq/concat_output \
  --total_concats 10 \
  --target_duration_min 20 \
  --target_duration_max 60 \
  --min_videos_per_concat 2 \
  --max_videos_per_concat 6 \
  --allow_reuse \
  --reuse_mode balanced \
  --max_usage_ratio 1.5
```

### 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `--video_metadata` | str | 指定包含所有视频元数据的 JSON 文件路径（必须） |
| `--output_dir` | str | 拼接后视频的保存路径（必须） |
| `--total_concats` | int | 生成的视频总数（必须） |
| `--target_duration_min` | float | 拼接后单个视频的最小目标时长（单位秒） |
| `--target_duration_max` | float | 拼接后单个视频的最大目标时长（单位秒） |
| `--min_videos_per_concat` | int | 每个拼接视频最少包含的视频数量 |
| `--max_videos_per_concat` | int | 每个拼接视频最多包含的视频数量 |
| `--allow_reuse` | action flag | 是否允许视频被多次使用 |
| `--reuse_mode` | str | 视频复用策略，支持 `balanced` 和 `random`（默认：balanced） |
| `--max_usage_ratio` | float | 单个视频最多可被使用的次数与拼接视频总数的比例上限 |
| `--seed` | int | 随机种子（控制可复现性，默认：42） |

## 输入数据格式

程序期望通过 `--video_metadata` 参数指定一个JSON文件，该文件包含所有视频的元数据信息。文件格式为列表，每一项包含以下字段：

```json
[
  {
    "video_id": "video_001",
    "duration": 21.4,
    "path": "/data1/whq/sample_videos/video_001.mp4"
  },
  {
    "video_id": "video_002",
    "duration": 45.1,
    "path": "/data1/whq/sample_videos/video_002.mp4"
  }
]
```

## 输出内容说明

程序会在 `--output_dir` 指定的目录中生成以下内容：

1. 一系列拼接后的视频文件，命名为 `concat_00000.mp4`, `concat_00001.mp4` 等
2. 一个 `concat_metadata.json` 文件，记录每个拼接视频由哪些原始视频组成及其顺序

输出的 `concat_metadata.json` 格式示例：

```json
[
  {
    "concat_video": "concat_00000.mp4",
    "videos": ["video_003", "video_014", "video_025"]
  },
  {
    "concat_video": "concat_00001.mp4",
    "videos": ["video_007", "video_032"]
  }
]
```

## 复用策略说明

### Balanced模式（默认）
在允许复用的情况下，优先选择使用次数较少的视频，以实现视频利用的均衡化。

### Random模式
在允许复用的情况下，随机选择视频进行拼接。

## 使用建议

1. 根据实际需求调整目标时长范围（默认20-60秒）
2. 合理设置复用比例，避免某些视频被过度使用
3. 使用固定的seed值以确保结果可复现
4. 根据视频库大小调整目标拼接数量