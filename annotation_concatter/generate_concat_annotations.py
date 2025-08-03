#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频拼接标注数据构造系统

该脚本基于现有的视频拼接策略与原始标注，构造拼接后视频的完整语义标注数据，
并借助大语言模型（LLM）自动生成衔接连贯的自然语言描述段落。
"""

import json
import os
import math
from typing import List, Dict, Any


def load_concat_plan(plan_file: str) -> List[Dict]:
    """
    加载拼接策略 JSON 文件
    
    Args:
        plan_file: 拼接策略文件路径
        
    Returns:
        拼接策略列表
    """
    with open(plan_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_video_descriptions(description_file: str) -> Dict[str, str]:
    """
    加载原始视频描述数据
    
    Args:
        description_file: 视频描述文件路径
        
    Returns:
        视频ID到描述的映射字典
    """
    video_descriptions = {}
    
    # 如果是jsonl文件，逐行读取
    if description_file.endswith('.jsonl'):
        with open(description_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line.strip())
                    # 移除.mp4后缀以匹配视频ID
                    video_id = data['video'].replace('.mp4', '')
                    # 提取GPT生成的描述
                    for conversation in data['conversations']:
                        if conversation['from'] == 'gpt':
                            video_descriptions[video_id] = conversation['value']
                            break
    else:
        # 如果是普通JSON文件
        with open(description_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                video_id = item.get('video_name', item.get('video_id', '')).replace('.mp4', '')
                if 'conversations' in item:
                    # 提取GPT生成的描述
                    for conversation in item['conversations']:
                        if conversation['from'] == 'gpt':
                            video_descriptions[video_id] = conversation['value']
                            break
                elif 'data' in item:
                    # 处理shot2story格式
                    summaries = [d['summary'] for d in item['data']]
                    video_descriptions[video_id] = ' '.join(summaries)
    
    return video_descriptions


def get_frame_paths(video_id: str, start_time: float, end_time: float, 
                   sample_frames_dir: str = '/data1/whq/sample_frames') -> List[str]:
    """
    根据时间范围获取帧图像路径列表
    
    Args:
        video_id: 视频ID
        start_time: 开始时间
        end_time: 结束时间
        sample_frames_dir: 采样帧目录
        
    Returns:
        帧图像路径列表
    """
    frame_dir = os.path.join(sample_frames_dir, video_id)
    if not os.path.exists(frame_dir):
        return []
    
    start_frame = int(start_time)
    end_frame = int(end_time)
    
    frame_paths = []
    for i in range(start_frame, end_frame + 1):
        frame_path = os.path.join(frame_dir, f'frame_{i:05d}.jpg')
        if os.path.exists(frame_path):
            frame_paths.append(frame_path)
    
    return frame_paths


def generate_transition_prompt(prev_summary: str, current_summary: str) -> str:
    """
    生成用于LLM的过渡提示词
    
    Args:
        prev_summary: 前一个视频片段的描述
        current_summary: 当前视频片段的描述
        
    Returns:
        过渡提示词
    """
    prompt = f'''请根据以下两个视频片段的文字描述，为拼接视频生成连贯、自然的描述内容：

第一个视频片段的内容如下：
"{prev_summary}"

当前视频片段的内容如下：
"{current_summary}"

请写出一段自然语言段落，重点描述当前片段的内容，同时简要提及前一片段，实现语义过渡与衔接。语言应简洁清晰、逻辑通顺，不要逐帧罗列，也不要虚构内容。'''

    return prompt


def process_concat_video(concat_item: Dict, video_descriptions: Dict[str, str]) -> Dict[str, Any]:
    """
    处理单个拼接视频，生成标注数据
    
    Args:
        concat_item: 拼接视频信息
        video_descriptions: 视频描述字典
        
    Returns:
        处理后的标注数据
    """
    concat_video_id = concat_item['concat_video'].replace('.mp4', '')
    
    result_data = []
    
    for i, boundary in enumerate(concat_item['boundaries']):
        video_id = boundary['video_id']
        start_time = boundary['start_time']
        end_time = boundary['end_time']
        
        # 获取视频描述
        summary = video_descriptions.get(video_id, "")
        
        # 对于非第一个片段，生成过渡提示（在实际应用中这里会调用LLM）
        if i > 0 and summary:
            prev_boundary = concat_item['boundaries'][i-1]
            prev_video_id = prev_boundary['video_id']
            prev_summary = video_descriptions.get(prev_video_id, "")
            
            if prev_summary and summary:
                # 在实际应用中，这里会调用LLM API
                # 为演示目的，我们直接生成一个简单的过渡描述
                transition_prompt = generate_transition_prompt(prev_summary, summary)
                # 模拟LLM响应
                summary = f"[TRANSITION] {summary}"
        
        result_data.append({
            "start": start_time,
            "end": end_time,
            "summary": summary
        })
    
    return {
        "video": concat_video_id,
        "data": result_data
    }


def generate_concat_annotations(concat_plan_file: str, 
                              video_descriptions_file: str,
                              output_file: str) -> None:
    """
    主函数：生成拼接视频标注数据
    
    Args:
        concat_plan_file: 拼接策略文件路径
        video_descriptions_file: 视频描述文件路径
        output_file: 输出文件路径
    """
    # 加载拼接策略
    print("加载拼接策略...")
    concat_plan = load_concat_plan(concat_plan_file)
    print(f"已加载 {len(concat_plan)} 个拼接视频策略")
    
    # 加载视频描述
    print("加载视频描述...")
    video_descriptions = load_video_descriptions(video_descriptions_file)
    print(f"已加载 {len(video_descriptions)} 个视频描述")
    
    # 处理每个拼接视频
    print("处理拼接视频...")
    results = []
    
    for i, concat_item in enumerate(concat_plan):
        print(f"处理 {i+1}/{len(concat_plan)}: {concat_item['concat_video']}")
        result = process_concat_video(concat_item, video_descriptions)
        results.append(result)
    
    # 保存结果
    print(f"保存结果到 {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("处理完成！")


def main():
    """
    主函数
    """
    # 文件路径配置
    concat_plan_file = '/data1/whq/concat_plan/concat_metadata.json'
    video_descriptions_file = '/data1/whq/sharegpt4o/video_conversations/gpt4o.jsonl'
    output_file = '/data1/whq/annotation_maker/annotation_concatter/concatenated_video_annotations.json'
    
    # 生成拼接标注
    generate_concat_annotations(concat_plan_file, video_descriptions_file, output_file)


if __name__ == "__main__":
    main()