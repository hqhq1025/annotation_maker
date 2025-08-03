#!/bin/bash

# 视频拼接程序使用示例

# 基本用法示例
echo "运行基本视频拼接示例..."
python3 concat_planer.py \
  --video_metadata /data1/whq/video_metadata.json \
  --output_dir ./output \
  --total_concats 10 \
  --target_duration_min 20 \
  --target_duration_max 60 \
  --min_videos_per_concat 2 \
  --max_videos_per_concat 4 \
  --allow_reuse \
  --reuse_mode balanced \
  --max_usage_ratio 1.5

echo "拼接完成！输出文件位于 ./output 目录中"

# 查看生成的元数据
echo "生成的拼接元数据:"
cat ./output/concat_metadata.json | head -20