#!/usr/bin/env python3
"""
多视频拼接策略程序
用于构造训练/评测用的拼接视频集
"""

import os
import json
import random
import argparse
from typing import List, Dict, Any
from collections import defaultdict
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VideoConcatenator:
    """
    视频拼接器类，用于根据指定策略拼接多个视频
    """
    
    def __init__(self, 
                 video_metadata: str,
                 output_dir: str,
                 total_concats: int = 500,
                 min_videos_per_concat: int = 2,
                 max_videos_per_concat: int = 4,
                 target_duration_min: float = 20.0,
                 target_duration_max: float = 60.0,
                 allow_reuse: bool = True,
                 reuse_mode: str = "balanced",
                 max_usage_ratio: float = 2.0,
                 seed: int = 42):
        """
        初始化视频拼接器
        
        Args:
            video_metadata: 包含所有视频元数据的 JSON 文件路径
            output_dir: 拼接后的视频及 metadata 输出路径
            total_concats: 目标拼接视频数量
            min_videos_per_concat: 每条拼接最少视频数
            max_videos_per_concat: 每条拼接最多视频数
            target_duration_min: 拼接结果的期望最短时长（秒）
            target_duration_max: 拼接结果的期望最长时长（秒）
            allow_reuse: 是否允许重复使用视频
            reuse_mode: 视频复用策略："balanced" 或 "random"
            max_usage_ratio: 单个视频最多使用次数与拼接视频总数的比例上限
            seed: 随机种子（控制可复现性）
        """
        self.video_metadata = video_metadata
        self.output_dir = output_dir
        self.total_concats = total_concats
        self.min_videos_per_concat = min_videos_per_concat
        self.max_videos_per_concat = max_videos_per_concat
        self.target_duration_min = target_duration_min
        self.target_duration_max = target_duration_max
        self.allow_reuse = allow_reuse
        self.reuse_mode = reuse_mode
        self.max_usage_ratio = max_usage_ratio
        self.seed = seed
        
        # 设置随机种子
        random.seed(seed)
        
        # 存储视频信息和使用次数
        self.videos = []
        self.video_usage_count = defaultdict(int)
        
        # 创建视频ID到视频信息的映射，便于快速查找
        self.video_map = {}
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 加载视频信息
        self._load_videos()
        
    def _load_videos(self):
        """
        从指定的JSON文件加载视频信息
        """
        logger.info("Loading video information...")
        
        try:
            with open(self.video_metadata, 'r') as f:
                raw_videos = json.load(f)
                
            # 转换现有格式到程序需要的格式
            for video in raw_videos:
                video_info = {
                    "video_id": video["video_name"],
                    "duration": video["duration_sec"],
                    "path": video["video_path"]
                }
                self.videos.append(video_info)
                self.video_map[video_info["video_id"]] = video_info
                
        except Exception as e:
            logger.error(f"Failed to load video metadata from {self.video_metadata}: {e}")
            raise
            
        logger.info(f"Loaded {len(self.videos)} videos")
        
        if len(self.videos) == 0:
            raise ValueError("No valid videos found in the specified metadata file")
            
    def _get_available_videos(self, current_duration: float = 0) -> List[Dict[str, Any]]:
        """
        根据当前已选视频的总时长，获取可用的视频列表
        
        Args:
            current_duration: 当前已选视频的总时长
            
        Returns:
            可用视频列表
        """
        # 计算剩余时长范围
        remaining_min = self.target_duration_min - current_duration
        remaining_max = self.target_duration_max - current_duration
        
        available_videos = []
        
        # 计算最大使用次数
        max_usage = self.total_concats * self.max_usage_ratio
        
        for video in self.videos:
            video_id = video['video_id']
            duration = video['duration']
            
            # 检查时长是否符合剩余时间要求
            # 视频时长必须大于等于剩余最小时间，且小于等于剩余最大时间
            if duration < remaining_min or duration > remaining_max:
                continue
                
            # 如果不允许复用，检查是否已使用
            if not self.allow_reuse and self.video_usage_count[video_id] > 0:
                continue
                
            # 如果允许复用，检查是否超过最大使用次数
            if self.allow_reuse and self.video_usage_count[video_id] >= max_usage and max_usage > 0:
                continue
                
            available_videos.append(video)
            
        return available_videos
    
    def _select_videos_for_concat(self) -> List[Dict[str, Any]]:
        """
        为一次拼接选择视频列表
        
        Returns:
            选中的视频列表
        """
        selected_videos = []
        current_duration = 0.0
        max_attempts = 100  # 防止无限循环
        attempts = 0
        
        # 随机确定本次拼接的视频数量
        target_video_count = random.randint(self.min_videos_per_concat, self.max_videos_per_concat)
        
        while len(selected_videos) < target_video_count and attempts < max_attempts:
            attempts += 1
            
            # 获取可用视频
            available_videos = self._get_available_videos(current_duration)
            
            if not available_videos:
                # 如果没有符合时长要求的视频，尝试放宽条件
                # 仅在当前时长较小时放宽条件，避免最终超出最大时长
                if current_duration < self.target_duration_min * 0.5:
                    available_videos = self._get_available_videos_relaxed(current_duration)
                
                if not available_videos:
                    break
                
            # 根据复用模式选择视频
            if self.reuse_mode == "balanced":
                # 优先选择使用次数最少的视频
                available_videos.sort(key=lambda v: self.video_usage_count[v['video_id']])
            elif self.reuse_mode == "random":
                # 随机打乱
                random.shuffle(available_videos)
                
            # 选择第一个视频（balanced模式下是使用次数最少的，random模式下是随机的）
            selected_video = available_videos[0]
            
            # 检查添加该视频后是否会超出最大时长
            if current_duration + selected_video['duration'] > self.target_duration_max:
                # 如果超出最大时长，则尝试寻找更小的视频
                smaller_videos = [v for v in available_videos 
                                if current_duration + v['duration'] <= self.target_duration_max]
                if smaller_videos:
                    selected_video = smaller_videos[0]
                else:
                    # 如果找不到合适的视频，结束当前拼接
                    break
            
            selected_videos.append(selected_video)
            current_duration += selected_video['duration']
            
            # 更新使用次数
            self.video_usage_count[selected_video['video_id']] += 1
            
        # 如果最终时长不满足最小要求，放弃该拼接
        if current_duration < self.target_duration_min:
            return []
            
        return selected_videos
    
    def _get_available_videos_relaxed(self, current_duration: float = 0) -> List[Dict[str, Any]]:
        """
        放宽条件获取可用视频列表（仅用于当前时长较小时）
        
        Args:
            current_duration: 当前已选视频的总时长
            
        Returns:
            可用视频列表
        """
        # 计算剩余时长范围
        remaining_min = self.target_duration_min - current_duration
        remaining_max = self.target_duration_max - current_duration
        
        available_videos = []
        
        # 计算最大使用次数
        max_usage = self.total_concats * self.max_usage_ratio
        
        for video in self.videos:
            video_id = video['video_id']
            duration = video['duration']
            
            # 放宽条件：只检查是否小于剩余最大时间
            if duration > remaining_max:
                continue
                
            # 如果不允许复用，检查是否已使用
            if not self.allow_reuse and self.video_usage_count[video_id] > 0:
                continue
                
            # 如果允许复用，检查是否超过最大使用次数
            if self.allow_reuse and self.video_usage_count[video_id] >= max_usage and max_usage > 0:
                continue
                
            available_videos.append(video)
            
        return available_videos
    
    def generate_concatenations(self) -> List[Dict[str, Any]]:
        """
        生成所有拼接视频
        
        Returns:
            拼接视频的元信息列表
        """
        logger.info("Generating video concatenations...")
        concatenations = []
        
        for i in range(self.total_concats):
            # 为每次拼接选择视频
            selected_videos = self._select_videos_for_concat()
            
            if not selected_videos:
                logger.warning(f"No videos selected for concat {i}, skipping...")
                continue
                
            # 计算总时长和每个视频的分界点
            total_duration = 0.0
            boundaries = []
            current_time = 0.0
            
            for video in selected_videos:
                boundaries.append({
                    "video_id": video["video_id"],
                    "start_time": current_time,
                    "end_time": current_time + video["duration"]
                })
                total_duration += video["duration"]
                current_time += video["duration"]
            
            # 创建拼接记录
            concat_record = {
                "concat_video": f"concat_{i:05d}.mp4",
                "total_duration": total_duration,
                "boundaries": boundaries,
                "videos": [video['video_id'] for video in selected_videos]
            }
            
            concatenations.append(concat_record)
            
            # 每100条记录输出一次进度
            if (i + 1) % 100 == 0:
                logger.info(f"Generated {i + 1}/{self.total_concats} concatenations")
                
        logger.info(f"Generated {len(concatenations)} concatenations")
        return concatenations
    
    def save_metadata(self, concatenations: List[Dict[str, Any]]):
        """
        保存拼接元信息到JSON文件
        
        Args:
            concatenations: 拼接视频的元信息列表
        """
        metadata_path = os.path.join(self.output_dir, "concat_metadata.json")
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(concatenations, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Metadata saved to {metadata_path}")
        
    def run(self):
        """
        运行视频拼接主流程
        """
        logger.info("Starting video concatenation process...")
        
        # 生成拼接视频
        concatenations = self.generate_concatenations()
        
        # 保存元信息
        self.save_metadata(concatenations)
        
        logger.info("Video concatenation process completed")


def main():
    """
    主函数，处理命令行参数并运行视频拼接器
    """
    parser = argparse.ArgumentParser(description="多视频拼接策略程序")
    parser.add_argument("--video_metadata", type=str, required=True, 
                        help="指定包含所有视频元数据的 JSON 文件路径")
    parser.add_argument("--output_dir", type=str, required=True, 
                        help="拼接后视频的保存路径")
    parser.add_argument("--total_concats", type=int, default=500, 
                        help="生成的视频总数")
    parser.add_argument("--min_videos_per_concat", type=int, default=2, 
                        help="每个拼接视频最少包含的视频数量")
    parser.add_argument("--max_videos_per_concat", type=int, default=4, 
                        help="每个拼接视频最多包含的视频数量")
    parser.add_argument("--target_duration_min", type=float, default=20.0, 
                        help="拼接后单个视频的最小目标时长（单位秒）")
    parser.add_argument("--target_duration_max", type=float, default=60.0, 
                        help="拼接后单个视频的最大目标时长（单位秒）")
    parser.add_argument("--allow_reuse", action="store_true", default=True, 
                        help="是否允许视频被多次使用")
    parser.add_argument("--no_allow_reuse", dest="allow_reuse", action="store_false", 
                        help="不允许视频被多次使用")
    parser.add_argument("--reuse_mode", type=str, choices=["balanced", "random"], default="balanced", 
                        help="视频复用策略，支持 balanced 和 random（默认：balanced）")
    parser.add_argument("--max_usage_ratio", type=float, default=2.0, 
                        help="单个视频最多可被使用的次数与拼接视频总数的比例上限")
    parser.add_argument("--seed", type=int, default=42, 
                        help="随机种子（控制可复现性）")
    
    args = parser.parse_args()
    
    # 创建并运行视频拼接器
    concatenator = VideoConcatenator(
        video_metadata=os.path.abspath(args.video_metadata),
        output_dir=os.path.abspath(args.output_dir),
        total_concats=args.total_concats,
        min_videos_per_concat=args.min_videos_per_concat,
        max_videos_per_concat=args.max_videos_per_concat,
        target_duration_min=args.target_duration_min,
        target_duration_max=args.target_duration_max,
        allow_reuse=args.allow_reuse,
        reuse_mode=args.reuse_mode,
        max_usage_ratio=args.max_usage_ratio,
        seed=args.seed
    )
    
    concatenator.run()


if __name__ == "__main__":
    main()
