#!/usr/bin/env python3
"""
视频元数据生成脚本
用于生成视频元数据文件，供拼接策略使用
"""

import os
import json
import argparse
from pathlib import Path
import cv2


def get_video_duration(video_path):
    """
    获取视频时长
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        视频时长（秒）
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return 0
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        return duration
    except Exception as e:
        print(f"获取视频 {video_path} 时长时出错: {e}")
        return 0


def generate_video_metadata(input_dir, output_file, min_duration=2.0):
    """
    生成视频元数据文件
    
    Args:
        input_dir: 包含视频文件的目录
        output_file: 输出元数据文件路径
        min_duration: 最小视频时长（秒）
    """
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录不存在: {input_dir}")
        return
    
    video_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
    
    if not video_files:
        print(f"警告: 在目录 {input_dir} 中未找到视频文件")
        # 创建空的元数据文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return
    
    print(f"找到 {len(video_files)} 个视频文件")
    
    video_metadata = []
    for i, video_file in enumerate(video_files):
        video_path = os.path.join(input_dir, video_file)
        video_name = Path(video_file).stem
        
        print(f"处理 {i+1}/{len(video_files)}: {video_file}")
        
        duration = get_video_duration(video_path)
        
        # 跳过时长过短的视频
        if duration < min_duration:
            print(f"  跳过 {video_file} (时长 {duration:.2f}s < {min_duration}s)")
            continue
            
        metadata = {
            "video_name": video_name,
            "duration_sec": duration,
            "video_path": os.path.abspath(video_path)
        }
        video_metadata.append(metadata)
    
    # 保存元数据文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(video_metadata, f, ensure_ascii=False, indent=2)
    
    print(f"元数据文件已生成: {output_file}")
    print(f"包含 {len(video_metadata)} 个视频")


def main():
    parser = argparse.ArgumentParser(description="生成视频元数据文件")
    parser.add_argument("--input_dir", required=True, help="包含视频文件的目录")
    parser.add_argument("--output_file", default="video_metadata.json", help="输出元数据文件路径")
    parser.add_argument("--min_duration", type=float, default=2.0, help="最小视频时长（秒）")
    
    args = parser.parse_args()
    
    generate_video_metadata(args.input_dir, args.output_file, args.min_duration)


if __name__ == "__main__":
    main()