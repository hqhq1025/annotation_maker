#!/bin/bash

# 视频拼接策略执行脚本
# 该脚本用于执行视频拼接策略，确保拼接数量分布均匀

set -e  # 遇到错误时停止执行

echo "开始执行视频拼接策略..."

# ========== 配置参数 ==========
WORKSPACE_ROOT="/data1/whq"
ANNOTATION_MAKER_DIR="$WORKSPACE_ROOT/annotation_maker"
CONCAT_PLANER_DIR="$ANNOTATION_MAKER_DIR/concat_planer"

# 输入参数
VIDEO_METADATA="${1:-$WORKSPACE_ROOT/sample_frames/video_metadata.json}"
OUTPUT_DIR="${2:-$CONCAT_PLANER_DIR/output}"

# 拼接参数
TOTAL_CONCATS="${3:-5000}"
MIN_VIDEOS_PER_CONCAT="${4:-2}"
MAX_VIDEOS_PER_CONCAT="${5:-6}"
TARGET_DURATION_MIN="${6:-20.0}"
TARGET_DURATION_MAX="${7:-120.0}"
REUSE_MODE="${8:-balanced}"
MAX_USAGE_RATIO="${9:-4.0}"

echo "参数配置:"
echo "  视频元数据文件: $VIDEO_METADATA"
echo "  输出目录: $OUTPUT_DIR"
echo "  拼接视频总数: $TOTAL_CONCATS"
echo "  每个拼接最少视频数: $MIN_VIDEOS_PER_CONCAT"
echo "  每个拼接最多视频数: $MAX_VIDEOS_PER_CONCAT"
echo "  目标最小时间: $TARGET_DURATION_MIN 秒"
echo "  目标最大时间: $TARGET_DURATION_MAX 秒"
echo "  复用模式: $REUSE_MODE"
echo "  最大使用比例: $MAX_USAGE_RATIO"

# 检查视频元数据文件是否存在
if [ ! -f "$VIDEO_METADATA" ]; then
    echo "错误: 视频元数据文件不存在: $VIDEO_METADATA"
    echo "请确保文件存在且为有效的JSON格式"
    exit 1
fi

# 检查视频元数据文件是否为空
if [ ! -s "$VIDEO_METADATA" ]; then
    echo "错误: 视频元数据文件为空: $VIDEO_METADATA"
    echo "请确保文件包含有效的视频元数据"
    exit 1
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# ========== 执行视频拼接 ==========
echo "执行视频拼接策略..."
python3 $CONCAT_PLANER_DIR/concat_planer.py \
  --video_metadata "$VIDEO_METADATA" \
  --output_dir "$OUTPUT_DIR" \
  --total_concats $TOTAL_CONCATS \
  --min_videos_per_concat $MIN_VIDEOS_PER_CONCAT \
  --max_videos_per_concat $MAX_VIDEOS_PER_CONCAT \
  --target_duration_min $TARGET_DURATION_MIN \
  --target_duration_max $TARGET_DURATION_MAX \
  --reuse_mode $REUSE_MODE \
  --max_usage_ratio $MAX_USAGE_RATIO \
  --allow_reuse

# ========== 输出结果统计 ==========
echo "拼接完成，生成的文件:"
echo "  1. 拼接后的视频文件: $OUTPUT_DIR/concat_*.mp4"
echo "  2. 拼接元数据文件: $OUTPUT_DIR/concat_metadata.json"

# 检查jq命令是否存在
if ! command -v jq &> /dev/null; then
    echo "提示: 未安装jq命令，无法显示详细统计信息"
    echo "在Ubuntu/Debian上安装: sudo apt-get install jq"
    echo "在CentOS/RHEL上安装: sudo yum install jq"
    exit 0
fi

# 统计生成的拼接视频数量
if [ -f "$OUTPUT_DIR/concat_metadata.json" ]; then
    GENERATED_COUNT=$(jq length "$OUTPUT_DIR/concat_metadata.json")
    echo "  3. 共生成 $GENERATED_COUNT 个拼接视频"
    
    # 统计各视频数量级别的分布
    echo "各视频数量级别的分布:"
    for i in $(seq $MIN_VIDEOS_PER_CONCAT $MAX_VIDEOS_PER_CONCAT); do
        COUNT=$(jq "[.[] | select(.videos | length == $i)] | length" "$OUTPUT_DIR/concat_metadata.json")
        echo "  包含 $i 个视频的拼接: $COUNT 个"
    done
else
    echo "警告: 未生成拼接元数据文件"
fi

echo "视频拼接策略执行完成！"