#!/usr/bin/env python3
"""
自动化脚本生成器，用于生成执行annotation_maker完整流程的脚本
"""

import argparse
import os
from pathlib import Path

def generate_pipeline_script(args):
    """
    生成执行整个annotation_maker流程的脚本
    """
    # 创建脚本内容
    script_content = f"""#!/bin/bash

# 视频标注生成流程自动化脚本
# 该脚本会按顺序执行所有步骤，生成训练数据

set -e  # 遇到错误时停止执行

echo "开始执行视频标注生成流程..."

# ========== 配置参数 ==========
WORKSPACE_ROOT="{os.path.abspath(args.workspace_root)}"
INPUT_VIDEOS_DIR="{os.path.abspath(args.input_videos_dir)}"
SAMPLE_FRAMES_DIR="{os.path.abspath(args.sample_frames_dir)}"
ANNOTATION_MAKER_DIR="{os.path.abspath(os.path.join(args.workspace_root, 'annotation_maker'))}"

# 视频采样参数
SAMPLING_INTERVAL={args.sampling_interval}
MIN_VIDEO_DURATION={args.min_video_duration}
NUM_WORKERS={args.num_workers}

# 视频拼接参数
TOTAL_CONCATS={args.total_concats}
MIN_VIDEOS_PER_CONCAT={args.min_videos_per_concat}
MAX_VIDEOS_PER_CONCAT={args.max_videos_per_concat}
TARGET_DURATION_MIN={args.target_duration_min}
TARGET_DURATION_MAX={args.target_duration_max}
REUSE_MODE="{args.reuse_mode}"
MAX_USAGE_RATIO={args.max_usage_ratio}

# ========== 步骤1: 视频帧采样 ==========
echo "步骤1: 视频帧采样"
mkdir -p "$SAMPLE_FRAMES_DIR"
python3 $ANNOTATION_MAKER_DIR/video_sampler/sample_videos.py \\
  --input_dir "$INPUT_VIDEOS_DIR" \\
  --output_dir "$SAMPLE_FRAMES_DIR" \\
  --metadata_path "$SAMPLE_FRAMES_DIR/video_metadata.json" \\
  --sampling_interval $SAMPLING_INTERVAL \\
  --min_duration $MIN_VIDEO_DURATION \\
  --num_workers $NUM_WORKERS

# ========== 步骤2: 生成拼接策略 ==========
echo "步骤2: 生成拼接策略"
CONCAT_PLAN_DIR="{os.path.abspath(os.path.join(args.workspace_root, 'annotation_maker', 'concat_planer'))}"
mkdir -p "$CONCAT_PLAN_DIR"
python3 $ANNOTATION_MAKER_DIR/concat_planer/concat_planer.py \\
  --video_metadata "$SAMPLE_FRAMES_DIR/video_metadata.json" \\
  --output_dir "$CONCAT_PLAN_DIR" \\
  --total_concats $TOTAL_CONCATS \\
  --min_videos_per_concat $MIN_VIDEOS_PER_CONCAT \\
  --max_videos_per_concat $MAX_VIDEOS_PER_CONCAT \\
  --target_duration_min $TARGET_DURATION_MIN \\
  --target_duration_max $TARGET_DURATION_MAX \\
  --reuse_mode $REUSE_MODE \\
  --max_usage_ratio $MAX_USAGE_RATIO

# ========== 步骤3: 构造拼接视频标注 ==========
echo "步骤3: 构造拼接视频标注"
ANNOTATION_CONCATTER_DIR="{os.path.abspath(os.path.join(args.workspace_root, 'annotation_maker', 'annotation_concatter'))}"
mkdir -p "$ANNOTATION_CONCATTER_DIR"
python3 $ANNOTATION_MAKER_DIR/annotation_concatter/generate_concat_annotations.py

# ========== 步骤4: 清理空summary数据 ==========
echo "步骤4: 清理空summary数据"
DATA_FILTER_DIR="{os.path.abspath(os.path.join(args.workspace_root, 'annotation_maker', 'data_filter'))}"
mkdir -p "$DATA_FILTER_DIR"
python3 $ANNOTATION_MAKER_DIR/data_filter/clean_empty_summaries.py

# ========== 步骤5: 生成对话格式训练数据 ==========
echo "步骤5: 生成对话格式训练数据"
CONVERSATION_MAKER_DIR="{os.path.abspath(os.path.join(args.workspace_root, 'annotation_maker', 'conversation_maker'))}"
mkdir -p "$CONVERSATION_MAKER_DIR"
python3 $ANNOTATION_MAKER_DIR/conversation_maker/generate_train_conversations.py

# ========== 步骤6: 数据统计分析 ==========
echo "步骤6: 数据统计分析"
STATISTIC_DIR="{os.path.abspath(os.path.join(args.workspace_root, 'annotation_maker', 'statistic'))}"
mkdir -p "$STATISTIC_DIR"
python3 $ANNOTATION_MAKER_DIR/statistic/analyze_concatenated_videos.py \\
  $ANNOTATION_CONCATTER_DIR/concatenated_video_annotations_cleaned.json \\
  -o $STATISTIC_DIR/analysis_result.txt

echo "所有步骤执行完成！"
echo "生成的文件:"
echo "1. 视频帧: $SAMPLE_FRAMES_DIR"
echo "2. 拼接策略: $CONCAT_PLAN_DIR/concat_metadata.json"
echo "3. 拼接视频标注: $ANNOTATION_CONCATTER_DIR/concatenated_video_annotations.json"
echo "4. 清理后标注: $ANNOTATION_CONCATTER_DIR/concatenated_video_annotations_cleaned.json"
echo "5. 训练对话数据: $CONVERSATION_MAKER_DIR/train_conversations.json"
echo "6. 统计分析结果: $STATISTIC_DIR/analysis_result.txt"
"""

    # 写入脚本文件
    script_path = os.path.join(os.path.abspath(args.workspace_root), args.output_script)
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 添加执行权限
    os.chmod(script_path, 0o755)
    
    print(f"脚本已生成: {script_path}")
    print(f"请运行 'bash {script_path}' 来执行整个流程")


def main():
    parser = argparse.ArgumentParser(description="生成annotation_maker流程执行脚本")
    parser.add_argument("--workspace_root", default="/data1/whq", 
                        help="工作区根目录")
    parser.add_argument("--input_videos_dir", required=True,
                        help="输入视频目录路径")
    parser.add_argument("--sample_frames_dir", default="/data1/whq/sample_frames",
                        help="采样帧输出目录路径")
    parser.add_argument("--output_script", default="run_annotation_pipeline.sh",
                        help="生成的脚本文件名")
    
    # 视频采样参数
    parser.add_argument("--sampling_interval", type=float, default=1.0,
                        help="采样间隔(秒)")
    parser.add_argument("--min_video_duration", type=float, default=2.0,
                        help="最小视频时长(秒)")
    parser.add_argument("--num_workers", type=int, default=8,
                        help="并行处理进程数")
    
    # 视频拼接参数
    parser.add_argument("--total_concats", type=int, default=500,
                        help="生成的拼接视频总数")
    parser.add_argument("--min_videos_per_concat", type=int, default=2,
                        help="每个拼接视频最少包含的视频数量")
    parser.add_argument("--max_videos_per_concat", type=int, default=6,
                        help="每个拼接视频最多包含的视频数量")
    parser.add_argument("--target_duration_min", type=float, default=20.0,
                        help="拼接视频的最小目标时长(秒)")
    parser.add_argument("--target_duration_max", type=float, default=60.0,
                        help="拼接视频的最大目标时长(秒)")
    parser.add_argument("--reuse_mode", choices=["balanced", "random"], default="balanced",
                        help="视频复用策略")
    parser.add_argument("--max_usage_ratio", type=float, default=2.0,
                        help="单个视频最多可被使用的次数与拼接视频总数的比例上限")
    
    args = parser.parse_args()
    
    generate_pipeline_script(args)


if __name__ == "__main__":
    main()