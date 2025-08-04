# 视频拼接策略程序

该程序用于将多个短视频拼接成较长的视频单元，主要用于构造训练/评测用的拼接视频集。

## 功能特点

1. **灵活拼接控制**：
   - 可自定义每个拼接视频包含的视频数量范围
   - 严格控制拼接视频的总时长范围
   - 保证每个视频在拼接中保持完整，不会被截断

2. **智能视频复用策略**：
   - 支持是否允许视频复用
   - 提供两种复用模式："balanced"（均衡使用）和"random"（随机选择）
   - 限制单个视频的最大使用次数，避免某些视频被过度使用

3. **严格的时长控制**：
   - 严格遵守用户设定的最小和最大时间范围
   - 智能放宽条件机制，避免因视频时长不匹配导致无法生成拼接视频
   - 自动检查和调整，确保最终拼接视频满足时长要求

4. **完整的元数据记录**：
   - 生成详细的拼接记录，包括每个拼接视频的组成
   - 输出为JSON格式，便于后续处理

5. **详细的统计信息**：
   - 自动生成拼接视频数量分布统计
   - 提供详细的时长统计信息（总时长、平均时长、最短/最长时长等）
   - 显示时长分布直方图
   - 检查生成的拼接视频是否符合时长要求

## 安装依赖

程序使用Python标准库编写，无需额外安装依赖：

```bash
python3 concat_planer.py --help
```

但为了处理视频文件，需要安装OpenCV：

```bash
pip install opencv-python
```

Shell脚本中使用了以下系统工具：
- `jq`: 用于解析和统计JSON数据
- `bc`: 用于浮点数计算

在Ubuntu/Debian上安装：
```bash
sudo apt-get install jq bc
```

在CentOS/RHEL上安装：
```bash
sudo yum install jq bc
```

## 使用方法

### 方法1：直接运行Python脚本

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

### 方法2：使用Shell脚本（推荐）

```bash
./run_balanced_concat.sh \
  /data1/whq/sample_videos/video_metadata.json \
  /data1/whq/concat_output \
  500 \
  2 \
  6 \
  20.0 \
  60.0 \
  balanced \
  2.0
```

Shell脚本会自动统计生成的拼接视频分布情况，确保数量分布均匀，并提供详细的时长统计信息。

### 方法3：生成视频元数据文件

如果视频元数据文件不存在或有问题，可以使用以下脚本生成：

```bash
python3 generate_video_metadata.py \
  --input_dir /path/to/your/videos \
  --output_file /path/to/video_metadata.json \
  --min_duration 2.0
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
    "video_name": "video_001",
    "duration_sec": 21.4,
    "video_path": "/data1/whq/sample_videos/video_001.mp4"
  },
  {
    "video_name": "video_002",
    "duration_sec": 45.1,
    "video_path": "/data1/whq/sample_videos/video_002.mp4"
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
    "total_duration": 55.23,
    "boundaries": [
      {
        "video_id": "video_003",
        "start_time": 0.0,
        "end_time": 21.4
      },
      {
        "video_id": "video_014",
        "start_time": 21.4,
        "end_time": 55.23
      }
    ],
    "videos": ["video_003", "video_014"]
  }
]
```

## 时长控制机制说明

为了严格遵守用户设定的时长范围（`target_duration_min` 到 `target_duration_max`），程序采用了以下机制：

1. **严格的视频筛选**：在选择每个视频时，程序会确保该视频的时长符合剩余时间的要求，避免最终结果超出最大时长。

2. **智能放宽机制**：当当前累积时长较小时，如果严格遵守时长限制会导致无法选择视频，程序会智能放宽条件以保证能够生成拼接视频。

3. **最终验证**：在完成视频选择后，程序会验证总时长是否满足最小要求，不满足的拼接视频会被丢弃。

4. **避免超长**：在添加视频前会检查是否会超出最大时长，如果会超出则尝试选择更短的视频或结束当前拼接。

这些机制确保了生成的拼接视频能够严格遵守用户设定的时长要求。

## 拼接数量分布说明

为了确保拼接数量分布均匀，程序采用以下策略：

1. **随机选择视频数量**：在用户指定的最小和最大视频数量之间随机选择每个拼接视频包含的视频数量。

2. **均衡复用模式**：当使用`balanced`复用模式时，程序会优先选择使用次数较少的视频，避免某些视频被过度使用。

3. **统计分析**：Shell脚本会自动统计生成的拼接视频在各视频数量级别的分布情况，确保分布相对均匀。

## 详细的统计信息

Shell脚本在执行完成后会自动生成以下统计信息：

1. **基本统计**：
   - 生成的拼接视频总数
   - 各视频数量级别的分布情况

2. **时长统计**：
   - 总时长（秒和小时）
   - 平均时长
   - 最短时长
   - 最长时长

3. **时长分布直方图**：
   - 0-30秒范围内的拼接视频数量
   - 30-60秒范围内的拼接视频数量
   - 60-90秒范围内的拼接视频数量
   - 90-120秒范围内的拼接视频数量
   - 120秒以上的拼接视频数量

4. **时长符合性检查**：
   - 检查生成的拼接视频是否都在用户设定的时长范围内
   - 报告不符合要求的拼接视频数量

这些统计信息可以帮助您快速了解生成的拼接视频的质量和特征，无需后续手动统计。

## 常见问题及解决方案

### 1. JSON解析错误

如果遇到 `JSONDecodeError` 错误，可能是视频元数据文件存在问题：

- 文件为空或格式不正确
- 文件内容不是有效的JSON格式

解决方案：
1. 检查元数据文件是否存在且不为空
2. 使用 `generate_video_metadata.py` 脚本重新生成元数据文件

### 2. 输出目录问题

如果发现脚本在指定目录下创建了额外的子目录，请检查：

- 确保传递给脚本的参数正确
- 检查路径中是否包含特殊字符或空格

### 3. 缺少依赖

如果提示缺少 `jq` 或 `bc` 命令，可以安装：

```bash
# Ubuntu/Debian
sudo apt-get install jq bc

# CentOS/RHEL
sudo yum install jq bc
```

`jq` 命令用于在Shell脚本中解析和统计JSON数据，`bc` 用于浮点数计算。如果未安装，脚本仍可正常运行，但不会显示详细的统计信息。