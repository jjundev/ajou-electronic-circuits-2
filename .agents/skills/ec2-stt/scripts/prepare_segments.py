#!/usr/bin/env python3
"""
Prepares audio segments and 1fps black MP4 wrappers for ec2-stt.

Splits input audio into safe chunks (default: 150s / 2.5 minutes) and wraps each chunk
into a 1fps black MP4 file concurrently for Gemini native multimodal perception.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys
import unicodedata


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def get_duration(file_path: str) -> float | None:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        dur_str = res.stdout.strip()
        if not dur_str:
            return None
        dur = float(dur_str)
        if dur <= 0.05:  # empty or unusable stub
            return None
        return dur
    except (subprocess.CalledProcessError, ValueError):
        return None


def wrap_mp4(mp3_path: str, mp4_path: str, duration: float) -> str:
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", "color=c=black:s=320x240:r=1",
        "-i", mp3_path,
        "-t", str(duration),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "128k",
        "-loglevel", "error",
        mp4_path,
    ]
    subprocess.run(cmd, check=True)
    return mp4_path


def prepare_segments(
    audio_path: str,
    work_dir: str,
    prefix: str,
    segment_seconds: int = 150,
    max_workers: int = 4,
) -> dict:
    audio_path = os.path.abspath(audio_path)
    work_dir = os.path.abspath(work_dir)
    os.makedirs(work_dir, exist_ok=True)

    total_duration = get_duration(audio_path)

    # 1. Segment audio into MP3s
    mp3_pattern = os.path.join(work_dir, f"{prefix}_part%02d.mp3")
    split_cmd = [
        "ffmpeg",
        "-y",
        "-i", audio_path,
        "-vn",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        "-f", "segment",
        "-segment_time", str(segment_seconds),
        "-segment_start_number", "1",
        "-reset_timestamps", "1",
        "-loglevel", "error",
        mp3_pattern,
    ]
    subprocess.run(split_cmd, check=True)

    # 2. Collect generated MP3s
    mp3_files = []
    for f in os.listdir(work_dir):
        fn = nfc(f)
        fpath = os.path.join(work_dir, f)
        if fn.startswith(prefix) and fn.endswith(".mp3") and "_part" in fn:
            if os.path.getsize(fpath) == 0:
                try:
                    os.remove(fpath)
                except OSError:
                    pass
                continue
            part_str = fn.split("_part")[-1].replace(".mp3", "")
            if part_str.isdigit():
                mp3_files.append((int(part_str), fpath))

    mp3_files.sort(key=lambda x: x[0])

    # 3. Filter valid MP3s and concurrently wrap each in a 1fps black MP4
    valid_files = []
    for part_num, mp3_p in mp3_files:
        dur = get_duration(mp3_p)
        if dur is None:
            try:
                os.remove(mp3_p)
            except OSError:
                pass
            continue
        valid_files.append((part_num, mp3_p, dur))

    segments = []
    wrap_tasks = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for part_num, mp3_p, dur in valid_files:
            mp4_p = mp3_p.rsplit(".", 1)[0] + "_temp.mp4"
            wrap_tasks.append((part_num, mp3_p, mp4_p, dur, executor.submit(wrap_mp4, mp3_p, mp4_p, dur)))

        for part_num, mp3_p, mp4_p, dur, fut in wrap_tasks:
            fut.result()  # raise if error
            segments.append({
                "part_num": part_num,
                "mp3_path": mp3_p,
                "mp4_path": mp4_p,
                "duration": round(dur, 2),
            })

    return {
        "audio_path": audio_path,
        "work_dir": work_dir,
        "prefix": prefix,
        "total_duration": round(total_duration, 2),
        "segment_seconds": segment_seconds,
        "num_segments": len(segments),
        "segments": segments,
    }


def main():
    parser = argparse.ArgumentParser(description="Segment audio and wrap into 1fps MP4s for ec2-stt")
    parser.add_argument("audio", help="Input audio file path")
    parser.add_argument("--work-dir", required=True, help="Directory to save segments")
    parser.add_argument("--prefix", required=True, help="Filename prefix (e.g. 1106 전회2)")
    parser.add_argument("--segment-seconds", type=int, default=150, help="Segment length in seconds (default: 150)")
    parser.add_argument("--max-workers", type=int, default=4, help="Max parallel ffmpeg wrapping workers")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")

    args = parser.parse_args()

    result = prepare_segments(
        audio_path=args.audio,
        work_dir=args.work_dir,
        prefix=args.prefix,
        segment_seconds=args.segment_seconds,
        max_workers=args.max_workers,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Successfully prepared {result['num_segments']} segments in {result['work_dir']}.")
        print(f"Total duration: {result['total_duration']}s, segment size: {result['segment_seconds']}s")


if __name__ == "__main__":
    main()
