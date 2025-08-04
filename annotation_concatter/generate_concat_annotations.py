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
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# 添加OpenAI库导入
from openai import OpenAI


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


def generate_transition_prompt(prev_summaries: List[tuple], current_summary: str) -> str:
    """
    生成用于LLM的过渡提示词，包含前面所有片段的信息
    
    Args:
        prev_summaries: 前面所有视频片段的描述列表，每个元素包含(视频ID, 描述)元组
        current_summary: 当前视频片段的描述
        
    Returns:
        过渡提示词
    """
    # 构建前面片段的描述文本
    if prev_summaries:
        # 限制历史片段数量，避免过长
        max_history = 3
        if len(prev_summaries) > max_history:
            # 只保留最近的几个片段
            prev_summaries = prev_summaries[-max_history:]
        
        history_str = "\n".join([
            f"Segment {i+1} (from video {video_id}):\n{summary}"
            for i, (video_id, summary) in enumerate(prev_summaries)
        ])
    else:
        history_str = "(No previous content)"
    
    current_str = current_summary
    
    prompt = f"""You are a video concatenation description assistant. You will receive:
1. **History**: Descriptions of previous video segments in a concatenated video (may be empty for the first segment).  
2. **Current**: Description of the current video segment.

Your task is to combine **Current** with **History** to produce one **short**, **coherent**, and **natural** paragraph summary (1–2 sentences) in a continuous storytelling style. The summary should:

- Seamlessly connect past and present content as a single narrative, referencing previous segments to create smooth transitions between scenes.
- For the third segment onwards, reference content from recent previous segments to maintain narrative continuity, but focus primarily on the current scene.
- Focus on describing **what has changed** or **what's new** in the current scene, while maintaining context from previous segments.
- When there are contextual connections between segments, clearly describe what has been added, changed, or is being done differently based on the previous content.
- **Do not** repeat objects, settings, or details already mentioned in **History** unless necessary for context.
- **Avoid** any atmospheric, emotional, or subjective commentary; describe the visual content **objectively**.
- **Do not** start with "This video…" or similar phrases.
- If **History** is empty, simply summarize **Current** on its own.
- Use varied and natural transition expressions instead of always using "following". Examples include:
  * "After organizing items in the kitchen, the scene shifts to..."
  * "Continuing the sequence, the video now shows..."
  * "Building upon the previous scenes of..., the current segment presents..."
  * "Transitioning from the earlier segment, we now see..."
  * "With the completion of... the focus moves to..."
  * "Having finished with..., the person now proceeds to..."
  * "The scene then changes to show..."
  * "Subsequently, the setting shifts to..."
- **Avoid** repetitive transitions or descriptions that simply restate what was already described in previous segments.
- **Focus** on how the current scene builds upon or differs from previous scenes rather than restating them.
- **Create** natural narrative flow by emphasizing the progression of activities or changes in setting.

Examples of good transitions:
- "After arranging objects in a box, the scene shifts to someone preparing a beverage in a kitchen."
- "Continuing from the previous segment where items were organized into bags, the person now moves to a different area to tidy up a pair of shoes."
- "Building upon the previous scenes of organizing items in the kitchen and packing belongings, the current segment shows a person carefully tying their shoelaces."
- "With the completion of organizing personal items into handbags, the focus now moves to a more personal grooming activity as the scene shows someone attending to their footwear."

---
### Input

History:
{history_str}

Current:
{current_str}

### Output
A single paragraph summary (1–2 sentences) in natural storytelling style, highlighting changes and maintaining narrative flow while avoiding repetition. No extra text."""

    return prompt


def call_llm_api(prompt: str) -> str:
    """
    调用大语言模型API生成过渡描述
    
    Args:
        prompt: 发送给大模型的提示词
        
    Returns:
        大模型生成的过渡描述
    """
    # 初始化OpenAI客户端
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="sk-526714df4c6047289b10011fe575d566",  # 如何获取API Key：https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    
    try:
        completion = client.chat.completions.create(
            model="qwen-plus",  # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant specialized in generating coherent video descriptions for concatenated videos.'},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.7,
            max_tokens=512
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"调用大模型API时出错: {e}")
        # 出错时返回原始描述加上过渡标记
        return f"[TRANSITION_ERROR] {prompt.split('Current:')[1].split('### Output')[0].strip()}"


def process_single_segment(i: int, boundaries: List[Dict], video_descriptions: Dict[str, str]) -> Dict[str, Any]:
    """
    处理单个视频片段
    
    Args:
        i: 片段索引
        boundaries: 所有边界信息
        video_descriptions: 视频描述字典
        
    Returns:
        处理后的片段数据
    """
    boundary = boundaries[i]
    video_id = boundary['video_id']
    start_time = boundary['start_time']
    end_time = boundary['end_time']
    
    # 获取视频描述
    summary = video_descriptions.get(video_id, "")
    
    # 对于非第一个片段，生成过渡提示并调用LLM
    if i > 0 and summary:
        # 收集前面所有片段的描述
        prev_summaries = []
        for j in range(i):
            prev_video_id = boundaries[j]['video_id']
            prev_summary = video_descriptions.get(prev_video_id, "")
            if prev_summary:
                prev_summaries.append((prev_video_id, prev_summary))
        
        if prev_summaries and summary:
            # 生成过渡提示词
            transition_prompt = generate_transition_prompt(prev_summaries, summary)
            # 调用大模型API
            summary = call_llm_api(transition_prompt)
    
    return {
        "video_id": video_id,
        "start": start_time,
        "end": end_time,
        "summary": summary
    }


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
    
    # 使用线程池并发处理每个片段，增加并发数到30
    with ThreadPoolExecutor(max_workers=30) as executor:
        # 提交所有任务
        future_to_index = {
            executor.submit(process_single_segment, i, concat_item['boundaries'], video_descriptions): i
            for i in range(len(concat_item['boundaries']))
        }
        
        # 收集结果
        results = [None] * len(concat_item['boundaries'])
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result()
                results[index] = result
            except Exception as e:
                print(f"处理片段 {index} 时出错: {e}")
                # 使用默认值填充
                boundary = concat_item['boundaries'][index]
                results[index] = {
                    "video_id": boundary['video_id'],
                    "start": boundary['start_time'],
                    "end": boundary['end_time'],
                    "summary": "[PROCESSING_ERROR]"
                }
        
        result_data = results
    
    return {
        "video": concat_video_id,
        "data": result_data
    }


def generate_concat_annotations(concat_plan_file: str, 
                              video_descriptions_file: str,
                              output_file: str,
                              max_workers: int = 30) -> None:
    """
    主函数：生成拼接视频标注数据
    
    Args:
        concat_plan_file: 拼接策略文件路径
        video_descriptions_file: 视频描述文件路径
        output_file: 输出文件路径
        max_workers: 并发处理的最大工作线程数
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
    
    # 使用线程池并发处理拼接视频，增加并发数到30
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_index = {
            executor.submit(process_concat_video, concat_item, video_descriptions): i
            for i, concat_item in enumerate(concat_plan)
        }
        
        # 收集结果
        processed_results = [None] * len(concat_plan)
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result()
                processed_results[index] = result
                print(f"已完成 {index+1}/{len(concat_plan)}: {concat_plan[index]['concat_video']}")
            except Exception as e:
                print(f"处理拼接视频 {index} 时出错: {e}")
                concat_item = concat_plan[index]
                concat_video_id = concat_item['concat_video'].replace('.mp4', '')
                # 使用默认值填充
                processed_results[index] = {
                    "video": concat_video_id,
                    "data": []
                }
        
        results = [r for r in processed_results if r is not None]
    
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
    concat_plan_file = '/data1/whq/annotation_maker/concat_planer/concat_metadata.json'
    video_descriptions_file = '/data1/whq/sharegpt4o/video_conversations/gpt4o.jsonl'
    output_file = '/data1/whq/annotation_maker/annotation_concatter/concatenated_video_annotations.json'
    
    # 生成拼接标注，使用更高的并发数
    generate_concat_annotations(os.path.abspath(concat_plan_file), 
                              os.path.abspath(video_descriptions_file),
                              os.path.abspath(output_file), 
                              max_workers=30)


if __name__ == "__main__":
    main()