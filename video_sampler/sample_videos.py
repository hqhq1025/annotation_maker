#!/usr/bin/env python3
"""
Video Frame Sampler & Metadata Generator

This tool samples frames from videos at regular intervals and generates metadata
for downstream processing in video understanding tasks.
"""

import argparse
import cv2
import json
import os
import sys
from pathlib import Path
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import functools


def sample_video_frames(video_info):
    """
    Sample frames from a video at regular intervals.
    
    Args:
        video_info (tuple): Tuple containing (video_path, output_dir, sampling_interval, min_duration)
        
    Returns:
        tuple: (video_metadata, failure_info) - One of them will be None
    """
    video_path, output_dir, sampling_interval, min_duration = video_info
    # Open video file
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        return None, {"video_name": Path(video_path).stem, 
                      "path": video_path, 
                      "reason": "Cannot open video"}
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    
    # Check if video meets minimum duration requirement
    if duration < min_duration:
        cap.release()
        return None, {"video_name": Path(video_path).stem, 
                      "path": video_path, 
                      "reason": f"Video duration ({duration:.2f}s) is less than minimum ({min_duration}s)"}
    
    # Create output directory for frames using absolute path
    os.makedirs(os.path.abspath(output_dir), exist_ok=True)
    
    # Calculate number of frames to sample
    expected_frames = int(duration / sampling_interval) + 1
    
    frames_metadata = []
    frame_index = 0
    timestamp = 0.0
    
    while timestamp <= duration:
        # Set video to the correct timestamp
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        
        # Read frame
        ret, frame = cap.read()
        if not ret:
            break
            
        # Save frame using absolute path
        frame_filename = f"frame_{frame_index:05d}.jpg"
        frame_path = os.path.join(os.path.abspath(output_dir), frame_filename)
        cv2.imwrite(frame_path, frame)
        
        # Record frame metadata
        frames_metadata.append({
            "frame_index": frame_index,
            "timestamp_sec": timestamp,
            "path": os.path.abspath(frame_path)
        })
        
        frame_index += 1
        timestamp += sampling_interval
    
    cap.release()
    
    # Compile video metadata
    video_metadata = {
        "video_name": Path(video_path).stem,
        "video_path": os.path.abspath(video_path),
        "fps": fps,
        "duration_sec": duration,
        "sampling_interval": sampling_interval,
        "expected_frames": expected_frames,
        "sampled_frames": len(frames_metadata),
        "frame_dir": os.path.abspath(output_dir),
        "frames": frames_metadata
    }
    
    return video_metadata, None


def main():
    parser = argparse.ArgumentParser(description="Sample video frames and generate metadata")
    parser.add_argument("--input_dir", required=True, help="Input directory containing video files")
    parser.add_argument("--output_dir", required=True, help="Output directory for sampled frames")
    parser.add_argument("--metadata_path", required=True, help="Path to output metadata JSON file")
    parser.add_argument("--sampling_interval", type=float, default=1.0, 
                        help="Sampling interval in seconds (default: 1.0)")
    parser.add_argument("--min_duration", type=float, default=0, 
                        help="Minimum video duration in seconds (default: 0)")
    parser.add_argument("--num_workers", type=int, default=None,
                        help="Number of worker processes (default: number of CPU cores)")
    
    args = parser.parse_args()
    
    # Check if input directory exists using absolute path
    if not os.path.exists(os.path.abspath(args.input_dir)):
        print(f"Error: Input directory '{args.input_dir}' does not exist")
        sys.exit(1)
    
    # Create output directory if it doesn't exist using absolute path
    os.makedirs(os.path.abspath(args.output_dir), exist_ok=True)
    
    # Find all MP4 videos in input directory
    video_files = [f for f in os.listdir(os.path.abspath(args.input_dir)) if f.lower().endswith('.mp4')]
    
    if not video_files:
        print(f"Warning: No MP4 files found in '{args.input_dir}'")
        # Create empty metadata file using absolute path
        with open(os.path.abspath(args.metadata_path), 'w') as f:
            json.dump([], f, indent=2)
        return
    
    print(f"Found {len(video_files)} video files to process")
    
    all_metadata = []
    failed_videos = []
    
    # Prepare video info for processing
    video_info_list = []
    for video_file in video_files:
        video_path = os.path.join(os.path.abspath(args.input_dir), video_file)
        video_name = Path(video_file).stem
        frame_output_dir = os.path.join(os.path.abspath(args.output_dir), video_name)
        video_info_list.append((video_path, frame_output_dir, args.sampling_interval, args.min_duration))
    
    # Determine number of worker processes
    num_workers = args.num_workers if args.num_workers else cpu_count()
    print(f"Using {num_workers} worker processes")
    
    all_metadata = []
    failed_videos = []
    
    # Process videos with progress bar
    with Pool(processes=num_workers) as pool:
        # Use functools.partial to pass the progress bar to the map function
        results = list(tqdm(
            pool.imap(process_single_video, video_info_list),
            total=len(video_info_list),
            desc="Processing videos"
        ))
    
    # Collect results
    for video_metadata, failure_info in results:
        if video_metadata:
            all_metadata.append(video_metadata)
        else:
            failed_videos.append(failure_info)
    
    # Write metadata to JSON file using absolute path
    with open(os.path.abspath(args.metadata_path), 'w') as f:
        json.dump(all_metadata, f, indent=2)
    
    # Write failed videos to JSON file
    failed_metadata_path = os.path.join(os.path.dirname(os.path.abspath(args.metadata_path)), "failed_videos.json")
    with open(os.path.abspath(failed_metadata_path), 'w') as f:
        json.dump({"failed_videos": failed_videos}, f, indent=2)
    
    print(f"\nProcessing complete!")
    print(f"  Successfully processed: {len(all_metadata)} videos")
    print(f"  Failed to process: {len(failed_videos)} videos")
    print(f"  Metadata saved to: {os.path.abspath(args.metadata_path)}")
    print(f"  Failed videos logged to: {os.path.abspath(failed_metadata_path)}")


def process_single_video(video_info):
    """
    Process a single video file - wrapper function for multiprocessing
    
    Args:
        video_info (tuple): Tuple containing (video_path, output_dir, sampling_interval, min_duration)
        
    Returns:
        tuple: (video_metadata, failure_info)
    """
    return sample_video_frames(video_info)


if __name__ == "__main__":
    main()