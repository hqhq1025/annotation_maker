#!/usr/bin/env python3
"""
交互式脚本生成器，通过问答方式收集参数并生成执行annotation_maker流程的脚本
"""

import os
import sys

def ask_question(question, default=None, required=False):
    """
    向用户提问并获取答案
    
    Args:
        question: 问题文本
        default: 默认值
        required: 是否必需
    
    Returns:
        用户的答案或默认值
    """
    if default is not None:
        question = f"{question} (默认: {default})"
    
    while True:
        answer = input(f"{question}: ").strip()
        
        # 如果用户直接回车且有默认值，使用默认值
        if not answer and default is not None:
            return default
        
        # 如果是必需的且用户没有输入，则继续询问
        if not answer and required:
            print("这是必需的参数，请输入。")
            continue
            
        return answer

def ask_yes_no_question(question, default=True):
    """
    向用户提问是/否问题
    
    Args:
        question: 问题文本
        default: 默认值 (True/False)
    
    Returns:
        True/False
    """
    default_text = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{question} [{default_text}]: ").strip().lower()
        
        if not answer:
            return default
            
        if answer in ['y', 'yes']:
            return True
        elif answer in ['n', 'no']:
            return False
        else:
            print("请输入 y/yes 或 n/no")

def collect_parameters():
    """
    通过问答方式收集所有参数
    
    Returns:
        包含所有参数的字典
    """
    print("=" * 60)
    print("欢迎使用 Annotation Maker 流程脚本生成器")
    print("我会通过问答方式收集参数，然后为您生成执行脚本")
    print("=" * 60)
    
    params = {}
    
    # 基本路径配置
    print("\n[基本路径配置]")
    params['workspace_root'] = ask_question(
        "工作区根目录", 
        default="/data1/whq", 
        required=True
    )
    
    params['input_videos_dir'] = ask_question(
        "输入视频目录路径", 
        required=True
    )
    
    params['sample_frames_dir'] = ask_question(
        "采样帧输出目录路径", 
        default=os.path.join(params['workspace_root'], "sample_frames"),
        required=True
    )
    
    params['output_script'] = ask_question(
        "生成的脚本文件名", 
        default="run_annotation_pipeline.sh",
        required=True
    )
    
    # 视频采样参数
    print("\n[视频采样参数]")
    params['sampling_interval'] = float(ask_question(
        "采样间隔(秒)", 
        default="1.0"
    ))
    
    params['min_video_duration'] = float(ask_question(
        "最小视频时长(秒)", 
        default="2.0"
    ))
    
    params['num_workers'] = int(ask_question(
        "并行处理进程数", 
        default="8"
    ))
    
    # 视频拼接参数
    print("\n[视频拼接参数]")
    params['total_concats'] = int(ask_question(
        "生成的拼接视频总数", 
        default="500"
    ))
    
    params['min_videos_per_concat'] = int(ask_question(
        "每个拼接视频最少包含的视频数量", 
        default="2"
    ))
    
    params['max_videos_per_concat'] = int(ask_question(
        "每个拼接视频最多包含的视频数量", 
        default="6"
    ))
    
    params['target_duration_min'] = float(ask_question(
        "拼接视频的最小目标时长(秒)", 
        default="20.0"
    ))
    
    params['target_duration_max'] = float(ask_question(
        "拼接视频的最大目标时长(秒)", 
        default="60.0"
    ))
    
    params['reuse_mode'] = ask_question(
        "视频复用策略 (balanced/random)", 
        default="balanced"
    )
    
    params['max_usage_ratio'] = float(ask_question(
        "单个视频最多可被使用的次数与拼接视频总数的比例上限", 
        default="2.0"
    ))
    
    # 确认参数
    print("\n" + "=" * 60)
    print("参数收集完成，以下是您的配置:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    
    print("=" * 60)
    
    if not ask_yes_no_question("确认使用以上参数生成脚本吗?"):
        print("用户取消操作")
        sys.exit(0)
    
    return params

def generate_pipeline_script(params):
    """
    根据参数生成执行脚本
    """
    # 创建脚本内容
    script_content = f"""#!/bin/bash

# 视频标注生成流程自动化脚本
# 该脚本会按顺序执行所有步骤，生成训练数据

set -e  # 遇到错误时停止执行

echo "开始执行视频标注生成流程..."

# ========== 配置参数 ==========
WORKSPACE_ROOT="{params['workspace_root']}"
INPUT_VIDEOS_DIR="{params['input_videos_dir']}"
SAMPLE_FRAMES_DIR="{params['sample_frames_dir']}"
ANNOTATION_MAKER_DIR="$WORKSPACE_ROOT/annotation_maker"

# 视频采样参数
SAMPLING_INTERVAL={params['sampling_interval']}
MIN_VIDEO_DURATION={params['min_video_duration']}
NUM_WORKERS={params['num_workers']}

# 视频拼接参数
TOTAL_CONCATS={params['total_concats']}
MIN_VIDEOS_PER_CONCAT={params['min_videos_per_concat']}
MAX_VIDEOS_PER_CONCAT={params['max_videos_per_concat']}
TARGET_DURATION_MIN={params['target_duration_min']}
TARGET_DURATION_MAX={params['target_duration_max']}
REUSE_MODE="{params['reuse_mode']}"
MAX_USAGE_RATIO={params['max_usage_ratio']}

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
CONCAT_PLAN_DIR="$ANNOTATION_MAKER_DIR/concat_planer"
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
ANNOTATION_CONCATTER_DIR="$ANNOTATION_MAKER_DIR/annotation_concatter"
mkdir -p "$ANNOTATION_CONCATTER_DIR"
python3 $ANNOTATION_MAKER_DIR/annotation_concatter/generate_concat_annotations.py

# ========== 步骤4: 清理空summary数据 ==========
echo "步骤4: 清理空summary数据"
DATA_FILTER_DIR="$ANNOTATION_MAKER_DIR/data_filter"
mkdir -p "$DATA_FILTER_DIR"
python3 $ANNOTATION_MAKER_DIR/data_filter/clean_empty_summaries.py

# ========== 步骤5: 生成对话格式训练数据 ==========
echo "步骤5: 生成对话格式训练数据"
CONVERSATION_MAKER_DIR="$ANNOTATION_MAKER_DIR/conversation_maker"
mkdir -p "$CONVERSATION_MAKER_DIR"
python3 $ANNOTATION_MAKER_DIR/conversation_maker/generate_train_conversations.py

# ========== 步骤6: 数据统计分析 ==========
echo "步骤6: 数据统计分析"
STATISTIC_DIR="$ANNOTATION_MAKER_DIR/statistic"
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
    script_path = os.path.join(params['workspace_root'], params['output_script'])
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 添加执行权限
    os.chmod(script_path, 0o755)
    
    print(f"\n脚本已生成: {script_path}")
    print(f"请运行 'bash {script_path}' 来执行整个流程")
    return script_path

def main():
    """
    主函数
    """
    # 收集参数
    params = collect_parameters()
    
    # 生成脚本
    script_path = generate_pipeline_script(params)
    
    # 询问是否立即执行
    print("\n" + "=" * 60)
    if ask_yes_no_question("是否立即执行生成的脚本?"):
        os.system(f"bash {script_path}")
    else:
        print("您可以稍后手动执行该脚本")

if __name__ == "__main__":
    main()