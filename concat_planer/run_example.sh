#!/bin/bash

# 视频拼接程序使用示例

echo "视频拼接程序使用示例"
echo "===================="

# 显示帮助信息
echo "1. 查看帮助信息:"
python3 concat_planer.py --help

echo -e "\n2. 基本使用示例:"
echo "运行视频拼接程序，生成10个拼接视频:"
echo "python3 concat_planer.py \\"
echo "  --video_metadata /data1/whq/video_metadata.json \\"
echo "  --output_dir ./output \\"
echo "  --total_concats 10 \\"
echo "  --target_duration_min 20 \\"
echo "  --target_duration_max 60 \\"
echo "  --min_videos_per_concat 2 \\"
echo "  --max_videos_per_concat 4 \\"
echo "  --allow_reuse \\"
echo "  --reuse_mode balanced \\"
echo "  --max_usage_ratio 1.5"

echo -e "\n3. 输出格式说明:"
echo "程序将生成以下内容:"
echo "  - 拼接视频文件: concat_00000.mp4, concat_00001.mp4, ..."
echo "  - 元数据文件: concat_metadata.json"
echo ""
echo "元数据文件包含每个拼接视频的详细信息，包括:"
echo "  - 总时长"
echo "  - 每个视频的分界点（开始和结束时间）"
echo "  - 组成视频的ID列表"