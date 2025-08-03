# Video Frame Sampler & Metadata Generator

This tool samples frames from videos at regular intervals and generates structured metadata for downstream processing in video understanding tasks such as QA generation, video concatenation, and trigger point detection.

## Features

- Samples frames from MP4 videos at configurable time intervals
- Generates structured metadata JSON with frame paths and timestamps
- Handles video corruption gracefully
- Filters videos by minimum duration
- Creates organized directory structure for output frames
- Parallel processing with multiprocessing for improved performance
- Progress bar to show processing status

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python sample_videos.py --input_dir <input_directory> --output_dir <output_directory> --metadata_path <metadata_file_path> [options]
```

### Arguments

- `--input_dir`: Path to directory containing MP4 video files
- `--output_dir`: Path to directory where sampled frames will be saved
- `--metadata_path`: Path where the metadata JSON file will be saved
- `--sampling_interval`: Sampling interval in seconds (default: 1.0)
- `--min_duration`: Minimum video duration in seconds (default: 0)
- `--num_workers`: Number of worker processes for parallel processing (default: number of CPU cores)

### Example

```bash
python sample_videos.py \
  --input_dir ./videos \
  --output_dir ./frames \
  --metadata_path ./video_metadata.json \
  --sampling_interval 1.0 \
  --min_duration 2.0 \
  --num_workers 8
```

This command will:
1. Process all MP4 files in `./videos`
2. Skip videos shorter than 2 seconds
3. Sample one frame per second
4. Use 8 worker processes for parallel processing
5. Save frames to subdirectories under `./frames`
6. Generate metadata in `./video_metadata.json`
7. Log any failed videos in `./failed_videos.json`

## Output Structure

The tool generates the following output structure:

```
<output_dir>/
├── video_001/
│   ├── frame_00000.jpg
│   ├── frame_00001.jpg
│   └── ...
├── video_002/
│   ├── frame_00000.jpg
│   ├── frame_00001.jpg
│   └── ...
└── metadata.json
```

## Metadata Format

### Video Metadata (video_metadata.json)

```json
[
  {
    "video_name": "sample_01",
    "video_path": "/path/to/input_dir/sample_01.mp4",
    "fps": 29.97,
    "duration_sec": 12.3,
    "sampling_interval": 1.0,
    "expected_frames": 12,
    "sampled_frames": 12,
    "frame_dir": "/path/to/output_dir/sample_01",
    "frames": [
      {
        "frame_index": 0,
        "timestamp_sec": 0.0,
        "path": "/path/to/output_dir/sample_01/frame_00000.jpg"
      },
      {
        "frame_index": 1,
        "timestamp_sec": 1.0,
        "path": "/path/to/output_dir/sample_01/frame_00001.jpg"
      }
    ]
  }
]
```

### Failed Videos (failed_videos.json)

```json
{
  "failed_videos": [
    {
      "video_name": "corrupted_video_001",
      "path": "/path/to/input_dir/corrupted_video_001.mp4",
      "reason": "Cannot open video"
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **OpenCV not installed**: Make sure you've run `pip install -r requirements.txt`

2. **Permission errors**: Ensure you have read permissions for input directory and write permissions for output directory

3. **No videos processed**: Check that your input directory contains MP4 files

4. **Corrupted video files**: The tool will skip corrupted videos and log them in failed_videos.json

### Performance Tips

- For large datasets, consider processing in batches
- SSD storage significantly improves processing speed
- Videos with higher frame rates may take longer to process
- Use `--num_workers` to adjust the number of parallel processes based on your CPU

## License

MIT