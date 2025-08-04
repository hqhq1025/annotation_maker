#!/usr/bin/env python3
"""
将视频拼接计划、原始视频标注和分布式图像帧合并为训练用对话格式JSON文件

输入:
1. 拼接策略文件 (concat_metadata.json)
2. 原始视频标注文件 (concatenated_video_annotations.json)
3. 图像帧路径 (sample_frames/ 目录下各视频子目录)

输出:
训练用对话格式JSON文件 (train_conversations.json)
"""

import os
import json
import math
import argparse
from typing import List, Dict, Any
from pathlib import Path


def load_concat_plan(plan_file: str) -> List[Dict]:
    """加载拼接计划文件"""
    with open(plan_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_video_annotations(annotation_file: str) -> Dict[str, List[Dict]]:
    """加载原始视频标注文件"""
    with open(annotation_file, 'r', encoding='utf-8') as f:
        raw_annotations = json.load(f)
    
    # 转换为以video_id为键的字典，方便查找
    annotations = {}
    for item in raw_annotations:
        concat_video_id = item['video']
        annotations[concat_video_id] = item['data']
    
    return annotations


def generate_train_conversations(concat_plan_file: str, 
                                annotation_file: str, 
                                sample_frames_dir: str,
                                output_file: str):
    """
    生成训练用对话格式JSON文件
    
    Args:
        concat_plan_file: 拼接计划文件路径
        annotation_file: 原始视频标注文件路径
        sample_frames_dir: 图像帧根目录路径
        output_file: 输出文件路径
    """
    
    # 加载输入文件
    concat_plans = load_concat_plan(concat_plan_file)
    video_annotations = load_video_annotations(annotation_file)
    
    # 结果存储
    train_conversations = []
    
    # 处理每个拼接视频
    for plan in concat_plans:
        concat_video_name = plan['concat_video']
        # 从拼接视频名称获取ID（去掉.mp4扩展名）
        concat_video_id = concat_video_name.replace('.mp4', '')
        boundaries = plan['boundaries']
        
        images = []
        conversations = []
        
        # 添加固定的首句
        conversations.append({
            "from": "human",
            "value": "请适当地描述一下视频中发生的内容"
        })
        
        # 获取该拼接视频的标注信息
        annotations = video_annotations.get(concat_video_id, [])
        
        # 创建一个字典，用于快速查找每个视频片段的summary
        video_summaries = {}
        for annotation in annotations:
            video_id = annotation['video_id']
            video_summaries[video_id] = annotation['summary']
        
        # 遍历每个边界片段
        for i, boundary in enumerate(boundaries):
            video_id = boundary['video_id']
            start_time = boundary['start_time']
            end_time = boundary['end_time']
            
            # 获取当前视频片段的summary
            current_summary = video_summaries.get(video_id)
            
            # 计算该片段的帧范围（相对于各自视频的帧索引）
            start_frame = 0  # 每个原始视频都从帧0开始
            end_frame = math.floor(end_time - start_time)  # 相对于该视频片段的帧数
            
            # 为每一秒添加帧和对话
            for frame_idx in range(start_frame, end_frame + 1):  # 包含end_frame
                # 构造图像路径（每个原始视频的帧都从0开始）
                image_path = f"{video_id}/frame_{frame_idx:05d}.jpg"
                images.append(image_path)
                
                # 添加图像对话
                conversations.append({
                    "from": "human",
                    "value": "<image>"
                })
                
                # 只有在当前视频片段的最后一帧才输出该视频的summary
                # 但最后一个视频片段的summary需要特殊处理
                if frame_idx == end_frame and current_summary and i < len(boundaries) - 1:
                    conversations.append({
                        "from": "gpt",
                        "value": f"<|response|> {current_summary}"
                    })
                else:
                    # 其他情况输出silent
                    conversations.append({
                        "from": "gpt",
                        "value": "<|silent|>"
                    })
        
        # 特殊处理最后一个视频片段
        if boundaries:
            # 添加最后一个图像帧
            last_boundary = boundaries[-1]
            last_video_id = last_boundary['video_id']
            last_start_time = last_boundary['start_time']
            last_end_time = last_boundary['end_time']
            last_frame_idx = math.floor(last_end_time - last_start_time)  # 相对于该视频片段的帧数
            last_image_path = f"{last_video_id}/frame_{last_frame_idx:05d}.jpg"
            images.append(last_image_path)
            
            # 添加最后一个图像对话
            conversations.append({
                "from": "human",
                "value": "<image>"
            })
            
            # 添加结束信号
            conversations.append({
                "from": "human",
                "value": "<|END_OF_STREAMING|>"
            })
            
            # 获取最后一个视频片段的summary并输出
            last_summary = video_summaries.get(last_video_id)
            if last_summary:
                conversations.append({
                    "from": "gpt",
                    "value": f"<|response|> {last_summary}"
                })
        
        # 添加到结果中
        train_conversations.append({
            "video": concat_video_name,
            "images": images,
            "conversations": conversations
        })
    
    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(train_conversations, f, ensure_ascii=False, indent=2)
    
    print(f"生成完成，共处理 {len(train_conversations)} 个拼接视频")
    print(f"结果保存至: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="生成训练用对话格式JSON文件")
    parser.add_argument("--concat_plan", 
                        default="/data1/whq/annotation_maker/concat_planer/concat_metadata.json",
                        help="拼接计划文件路径")
    parser.add_argument("--annotations", 
                        default="/data1/whq/annotation_maker/annotation_concatter/concatenated_video_annotations.json",
                        help="原始视频标注文件路径")
    parser.add_argument("--sample_frames_dir", 
                        default="/data1/whq/sample_frames",
                        help="图像帧根目录路径")
    parser.add_argument("--output", 
                        default="/data1/whq/annotation_maker/annotation_concatter/train_conversations.json",
                        help="输出文件路径")
    
    args = parser.parse_args()
    
    generate_train_conversations(
        args.concat_plan,
        args.annotations,
        args.sample_frames_dir,
        args.output
    )


if __name__ == "__main__":
    main()