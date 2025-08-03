#!/usr/bin/env python3
"""
测试视频拼接程序
"""

import json
import os
import sys
import shutil

# 将上级目录添加到Python路径中，以便导入concat_planer模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from concat_planer import VideoConcatenator
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_metadata(test_file_path):
    """
    创建测试用的视频元数据文件
    """
    test_metadata = [
        {
            "video_name": "test_video_1",
            "video_path": "/data1/whq/test_videos/test_video_1.mp4",
            "duration_sec": 15.5,
            "fps": 30.0,
            "frames": []
        },
        {
            "video_name": "test_video_2",
            "video_path": "/data1/whq/test_videos/test_video_2.mp4",
            "duration_sec": 25.0,
            "fps": 30.0,
            "frames": []
        },
        {
            "video_name": "test_video_3",
            "video_path": "/data1/whq/test_videos/test_video_3.mp4",
            "duration_sec": 35.2,
            "fps": 30.0,
            "frames": []
        },
        {
            "video_name": "test_video_4",
            "video_path": "/data1/whq/test_videos/test_video_4.mp4",
            "duration_sec": 10.8,
            "fps": 30.0,
            "frames": []
        }
    ]
    
    with open(test_file_path, 'w') as f:
        json.dump(test_metadata, f, indent=2)


def test_concatenator():
    """
    测试视频拼接器
    """
    # 创建测试目录
    test_dir = "test_output"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建测试元数据文件
    test_metadata_path = os.path.join(test_dir, "test_metadata.json")
    create_test_metadata(test_metadata_path)
    
    try:
        # 创建视频拼接器实例
        concatenator = VideoConcatenator(
            video_metadata=test_metadata_path,
            output_dir=test_dir,
            total_concats=5,
            min_videos_per_concat=2,
            max_videos_per_concat=3,
            target_duration_min=20.0,
            target_duration_max=60.0,
            allow_reuse=True,
            reuse_mode="balanced",
            max_usage_ratio=1.5,
            seed=42
        )
        
        # 运行拼接器
        logger.info("开始运行视频拼接器")
        concatenator.run()
        
        # 检查输出文件
        metadata_path = os.path.join(test_dir, "concat_metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                logger.info(f"成功生成 {len(metadata)} 个拼接视频记录")
                logger.info("示例记录:")
                logger.info(json.dumps(metadata[0], indent=2, ensure_ascii=False))
                
                # 验证新添加的字段
                sample_record = metadata[0]
                assert "total_duration" in sample_record, "缺少total_duration字段"
                assert "boundaries" in sample_record, "缺少boundaries字段"
                assert len(sample_record["boundaries"]) > 0, "boundaries为空"
                        
                logger.info("输出数据验证通过")
        else:
            logger.error("未找到输出的元数据文件")
            
    finally:
        # 清理测试文件（注释掉以便查看测试结果）
        # cleanup_test_files(test_dir)
        pass


def cleanup_test_files(test_dir):
    """
    清理测试文件
    """
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        logger.info(f"已清理测试文件目录: {test_dir}")


if __name__ == "__main__":
    test_concatenator()