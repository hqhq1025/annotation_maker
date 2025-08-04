import json
import numpy as np
from collections import Counter
import sys
from datetime import datetime

def analyze_concatenated_videos(file_path, output_file=None):
    """
    分析clean后的拼接视频标注文件，统计拼接视频时长分布、元视频数量分布等信息
    """
    # 保存原始stdout
    original_stdout = sys.stdout
    
    # 如果指定了输出文件，则重定向输出
    if output_file:
        sys.stdout = open(output_file, 'w')
    
    try:
        # 读取数据
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # 统计信息
        total_durations = []  # 拼接视频总时长
        video_counts = []     # 每个拼接视频包含的元视频数量
        single_video_durations = []  # 单个元视频的时长
        
        print(f"总共 {len(data)} 个拼接视频")
        
        for concat_video in data:
            # 计算拼接视频总时长
            concat_data = concat_video['data']
            total_duration = concat_data[-1]['end'] if concat_data else 0
            total_durations.append(total_duration)
            
            # 计算元视频数量
            video_count = len(concat_data)
            video_counts.append(video_count)
            
            # 收集单个元视频时长
            for video in concat_data:
                duration = video['end'] - video['start']
                single_video_durations.append(duration)
        
        # 输出统计信息
        print("\n=== 拼接视频时长分布 ===")
        print(f"总时长: {np.sum(total_durations):.2f} 秒 ({np.sum(total_durations)/3600:.2f} 小时)")
        print(f"平均时长: {np.mean(total_durations):.2f} 秒")
        print(f"最短时长: {np.min(total_durations):.2f} 秒")
        print(f"最长时长: {np.max(total_durations):.2f} 秒")
        print(f"时长中位数: {np.median(total_durations):.2f} 秒")
        print(f"时长标准差: {np.std(total_durations):.2f} 秒")
        
        print("\n=== 元视频数量分布 ===")
        video_count_counter = Counter(video_counts)
        for count, freq in sorted(video_count_counter.items()):
            print(f"包含 {count} 个元视频的拼接视频有 {freq} 个 ({freq/len(data)*100:.2f}%)")
        print(f"平均每拼接视频包含元视频数: {np.mean(video_counts):.2f}")
        print(f"最少元视频数: {np.min(video_counts)}")
        print(f"最多元视频数: {np.max(video_counts)}")
        
        print("\n=== 元视频时长分布 ===")
        print(f"平均时长: {np.mean(single_video_durations):.2f} 秒")
        print(f"最短时长: {np.min(single_video_durations):.2f} 秒")
        print(f"最长时长: {np.max(single_video_durations):.2f} 秒")
        print(f"时长中位数: {np.median(single_video_durations):.2f} 秒")
        print(f"时长标准差: {np.std(single_video_durations):.2f} 秒")
        
        # 按时长区间统计
        duration_ranges = [0, 30, 60, 90, 120, 150, 180, 210, 240, float('inf')]
        duration_labels = ['0-30s', '30-60s', '60-90s', '90-120s', '120-150s', '150-180s', '180-210s', '210-240s', '240s+']
        
        # 统计每个区间的数量
        duration_counts = [0] * len(duration_ranges)
        for duration in total_durations:
            for i, range_limit in enumerate(duration_ranges):
                if duration < range_limit:
                    duration_counts[i] += 1
                    break
        
        print("\n=== 拼接视频时长区间分布 ===")
        for i, (label, count) in enumerate(zip(duration_labels, duration_counts)):
            print(f"{label:8}: {count:4} ({count/len(data)*100:5.2f}%)")
        
        # 按元视频数量区间统计
        count_ranges = list(range(1, 11)) + [float('inf')]
        count_labels = [str(i) for i in range(1, 10)] + ['10+']
        
        # 统计每个区间的数量
        count_counts = [0] * len(count_ranges)
        for count in video_counts:
            for i, range_limit in enumerate(count_ranges):
                if count < range_limit:
                    count_counts[i] += 1
                    break
        
        print("\n=== 拼接视频包含元视频数量分布 ===")
        for i, (label, count) in enumerate(zip(count_labels, count_counts)):
            print(f"{label:>4}个元视频: {count:4} ({count/len(data)*100:5.2f}%)")
            
    finally:
        # 恢复原始stdout
        if output_file:
            sys.stdout.close()
            sys.stdout = original_stdout

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='分析拼接视频标注文件')
    parser.add_argument('input_file', nargs='?', default="concatenated_video_annotations_cleaned.json", 
                        help='输入的JSON文件路径')
    parser.add_argument('-o', '--output', default=None, help='输出的文本文件路径')
    
    args = parser.parse_args()
    
    # 默认输出到txt文件
    output_file = args.output
    if output_file is None:
        # 如果没有指定输出文件，使用默认名称
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"concatenated_video_analysis_{timestamp}.txt"
    
    analyze_concatenated_videos(args.input_file, output_file)
    print(f"分析完成，结果已保存到 {output_file}")