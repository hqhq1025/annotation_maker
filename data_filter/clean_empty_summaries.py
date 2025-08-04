#!/usr/bin/env python3
"""
清理程序：去除包含空summary的拼接视频

该程序用于清理concatenated_video_annotations.json文件，
如果拼接视频中包含任何空summary的元视频片段，则移除整个拼接视频，
以确保训练数据的质量。
"""

import json
import argparse
from typing import List, Dict, Any


def load_annotations(annotation_file: str) -> List[Dict]:
    """加载原始视频标注文件"""
    with open(annotation_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_annotations(annotations: List[Dict], output_file: str):
    """保存清理后的视频标注文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, ensure_ascii=False, indent=2)


def has_empty_summary(concat_video: Dict) -> bool:
    """
    检查拼接视频是否包含空summary的片段
    
    Args:
        concat_video: 拼接视频数据
        
    Returns:
        如果包含空summary则返回True，否则返回False
    """
    for video_data in concat_video["data"]:
        if not video_data.get("summary", "").strip():
            return True
    return False


def clean_empty_summaries(annotations: List[Dict]) -> List[Dict]:
    """
    清理包含空summary的拼接视频
    
    Args:
        annotations: 原始视频标注数据
        
    Returns:
        清理后的视频标注数据
    """
    cleaned_annotations = []
    removed_count = 0
    
    for concat_video in annotations:
        # 检查拼接视频是否包含空summary的片段
        if has_empty_summary(concat_video):
            # 如果包含空summary，则移除整个拼接视频
            removed_count += 1
            print(f"移除包含空summary的拼接视频: {concat_video['video']}")
            
            # 打印被移除的空summary片段信息
            for video_data in concat_video["data"]:
                if not video_data.get("summary", "").strip():
                    print(f"  - 空summary片段: {video_data['video_id']}, "
                          f"时间范围 {video_data['start']}-{video_data['end']}")
        else:
            # 如果不包含空summary，则保留该拼接视频
            cleaned_annotations.append(concat_video)
    
    print(f"总共移除了 {removed_count} 个包含空summary的拼接视频")
    return cleaned_annotations


def main():
    parser = argparse.ArgumentParser(description="清理包含空summary的拼接视频")
    parser.add_argument("--input", 
                        default="/data1/whq/annotation_maker/annotation_concatter/concatenated_video_annotations.json",
                        help="输入的视频标注文件路径")
    parser.add_argument("--output", 
                        default="/data1/whq/annotation_maker/annotation_concatter/concatenated_video_annotations_cleaned.json",
                        help="输出的清理后视频标注文件路径")
    
    args = parser.parse_args()
    
    # 加载原始标注文件
    print("加载原始视频标注文件...")
    annotations = load_annotations(args.input)
    print(f"原始文件包含 {len(annotations)} 个拼接视频")
    
    # 清理包含空summary的拼接视频
    print("清理包含空summary的拼接视频...")
    cleaned_annotations = clean_empty_summaries(annotations)
    print(f"清理后剩余 {len(cleaned_annotations)} 个拼接视频")
    
    # 保存清理后的文件
    print("保存清理后的视频标注文件...")
    save_annotations(cleaned_annotations, args.output)
    print(f"清理后的文件已保存至: {args.output}")


if __name__ == "__main__":
    main()