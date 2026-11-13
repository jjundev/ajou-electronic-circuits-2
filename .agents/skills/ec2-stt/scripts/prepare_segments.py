#!/usr/bin/env python3
"""
Prepares audio segments and 1fps black MP4 wrappers for ec2-stt.

Supports:
1. Silence-aware segmentation (default: 50s target, +/-12s silence search window)
   with concurrent 1fps black MP4 wrapping and start_time manifest generation.
2. One-command resplitting (--resplit) of a safety-filter-blocked MP3 chunk into
   N equal subchunks wrapped in 1fps black MP4s.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
import re
import subprocess
import sys
import unicodedata


SILENCE_START_RE = re.compile(r"silence_start:\s*([0-9.]+)")
SILENCE_END_RE = re.compile(r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)")


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def get_duration(file_path: str) -> float | None:
    """Return audio duration in seconds via ffprobe, or None if invalid/empty."""
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
        if dur <= 0.05:
            return None
        return dur
    except (subprocess.CalledProcessError, ValueError):
        return None


def detect_silences(
    audio_path: str,
    noise_db: float = -35.0,
    min_silence_dur: float = 0.4,
) -> list[tuple[float, float, float]]:
    """Detect silence intervals as (start, end, duration) using ffmpeg silencedetect."""
    cmd = [
        "ffmpeg",
        "-i", audio_path,
        "-af", f"silencedetect=noise={noise_db}dB:d={min_silence_dur}",
        "-f", "null",
        "-",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    silences: list[tuple[float, float, float]] = []
    pending_start: float | None = None

    for line in res.stderr.splitlines():
        m_start = SILENCE_START_RE.search(line)
        if m_start:
            pending_start = float(m_start.group(1))
            continue
        m_end = SILENCE_END_RE.search(line)
        if m_end and pending_start is not None:
            end = float(m_end.group(1))
            dur = float(m_end.group(2))
            silences.append((pending_start, end, dur))
            pending_start = None

    return silences


def compute_cut_points(
    total_duration: float,
    target_seconds: int,
    window_seconds: int,
    silences: list[tuple[float, float, float]],
) -> list[float]:
    """Choose silence-aligned cut timestamps within [target - window, target + window]."""
    cut_points: list[float] = []
    cursor = 0.0
    min_chunk = max(10.0, float(target_seconds - window_seconds))

    while cursor + target_seconds + window_seconds < total_duration:
        low = cursor + min_chunk
        high = min(cursor + target_seconds + window_seconds, total_duration - 5.0)
        candidates = []
        for start, end, dur in silences:
            mid = (start + end) / 2.0
            if low <= mid <= high:
                candidates.append((dur, -abs(mid - (cursor + target_seconds)), mid))

        if candidates:
            candidates.sort(reverse=True)
            cut = round(candidates[0][2], 3)
        else:
            cut = round(cursor + target_seconds, 3)

        if cut <= cursor + 1.0 or cut >= total_duration - 1.0:
            break
        cut_points.append(cut)
        cursor = cut

    return cut_points


def wrap_mp4(mp3_path: str, mp4_path: str, duration: float) -> str:
    """Wrap an MP3 chunk in a 1fps black MP4 matching its exact duration."""
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


def wrap_chunks_concurrently(
    items: list[tuple[int, str, float, float]],
    max_workers: int,
) -> list[dict]:
    """Wrap (index, mp3_path, start_time, duration) tuples into 1fps MP4s in parallel."""
    segments: list[dict] = []
    tasks = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for idx, mp3_p, start_time, dur in items:
            mp4_p = mp3_p.rsplit(".", 1)[0] + "_temp.mp4"
            tasks.append((idx, mp3_p, mp4_p, start_time, dur, executor.submit(wrap_mp4, mp3_p, mp4_p, dur)))

        for idx, mp3_p, mp4_p, start_time, dur, fut in tasks:
            fut.result()
            segments.append({
                "part_num": idx,
                "mp3_path": mp3_p,
                "mp4_path": mp4_p,
                "start_time": round(start_time, 3),
                "duration": round(dur, 2),
            })
    return segments


def prepare_segments(
    audio_path: str,
    work_dir: str,
    prefix: str,
    segment_seconds: int = 50,
    window_seconds: int = 12,
    max_workers: int = 4,
) -> dict:
    """Segment audio (silence-aware when window_seconds > 0) and wrap each chunk as 1fps MP4."""
    audio_path = os.path.abspath(audio_path)
    work_dir = os.path.abspath(work_dir)
    os.makedirs(work_dir, exist_ok=True)

    total_duration = get_duration(audio_path)
    if total_duration is None:
        raise RuntimeError(f"Could not read valid duration for {audio_path}")

    cut_points: list[float] = []
    if window_seconds > 0:
        silences = detect_silences(audio_path)
        cut_points = compute_cut_points(total_duration, segment_seconds, window_seconds, silences)

    mp3_pattern = os.path.join(work_dir, f"{prefix}_part%02d.mp3")
    if window_seconds > 0 and not cut_points:
        # Audio fits in a single segment
        single_mp3 = os.path.join(work_dir, f"{prefix}_part01.mp3")
        split_cmd = [
            "ffmpeg", "-y", "-i", audio_path, "-vn",
            "-c:a", "libmp3lame", "-b:a", "192k", "-loglevel", "error", single_mp3,
        ]
    elif cut_points:
        split_cmd = [
            "ffmpeg", "-y", "-i", audio_path, "-vn",
            "-c:a", "libmp3lame", "-b:a", "192k",
            "-f", "segment",
            "-segment_times", ",".join(str(t) for t in cut_points),
            "-segment_start_number", "1",
            "-reset_timestamps", "1",
            "-loglevel", "error",
            mp3_pattern,
        ]
    else:
        split_cmd = [
            "ffmpeg", "-y", "-i", audio_path, "-vn",
            "-c:a", "libmp3lame", "-b:a", "192k",
            "-f", "segment",
            "-segment_time", str(segment_seconds),
            "-segment_start_number", "1",
            "-reset_timestamps", "1",
            "-loglevel", "error",
            mp3_pattern,
        ]
    subprocess.run(split_cmd, check=True)

    part_re = re.compile(rf"^{re.escape(nfc(prefix))}_part(\d+)\.mp3$")
    mp3_files: list[tuple[int, str]] = []
    for f in os.listdir(work_dir):
        fn = nfc(f)
        m = part_re.match(fn)
        if not m:
            continue
        fpath = os.path.join(work_dir, f)
        if os.path.getsize(fpath) == 0:
            try:
                os.remove(fpath)
            except OSError:
                pass
            continue
        mp3_files.append((int(m.group(1)), fpath))

    mp3_files.sort(key=lambda x: x[0])

    valid_items: list[tuple[int, str, float, float]] = []
    cumulative_start = 0.0
    for part_num, mp3_p in mp3_files:
        dur = get_duration(mp3_p)
        if dur is None:
            try:
                os.remove(mp3_p)
            except OSError:
                pass
            continue
        start_time = ([0.0] + cut_points)[part_num - 1] if cut_points and (part_num - 1) < len(cut_points) + 1 else cumulative_start
        valid_items.append((part_num, mp3_p, start_time, dur))
        cumulative_start += dur

    segments = wrap_chunks_concurrently(valid_items, max_workers=max_workers)

    return {
        "audio_path": audio_path,
        "work_dir": work_dir,
        "prefix": prefix,
        "total_duration": round(total_duration, 2),
        "segment_seconds": segment_seconds,
        "window_seconds": window_seconds,
        "silence_aware": window_seconds > 0,
        "num_segments": len(segments),
        "segments": segments,
    }


def resplit_chunk(mp3_path: str, parts: int = 3, max_workers: int = 4) -> dict:
    """Split a failing MP3 chunk into N equal subchunks and wrap each as 1fps MP4."""
    mp3_path = os.path.abspath(mp3_path)
    total_dur = get_duration(mp3_path)
    if total_dur is None:
        raise RuntimeError(f"Could not read valid duration for {mp3_path}")

    stem = mp3_path.rsplit(".", 1)[0]
    sub_dur = total_dur / parts
    cut_points = [round(i * sub_dur, 3) for i in range(1, parts)]
    sub_pattern = f"{stem}_%d.mp3"

    cmd = [
        "ffmpeg", "-y",
        "-i", mp3_path,
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        "-f", "segment",
        "-segment_times", ",".join(str(t) for t in cut_points),
        "-segment_start_number", "1",
        "-reset_timestamps", "1",
        "-loglevel", "error",
        sub_pattern,
    ]
    subprocess.run(cmd, check=True)

    items: list[tuple[int, str, float, float]] = []
    starts = [0.0] + cut_points
    for idx in range(1, parts + 1):
        sub_mp3 = f"{stem}_{idx}.mp3"
        if not os.path.isfile(sub_mp3):
            continue
        actual_dur = get_duration(sub_mp3)
        if actual_dur is not None:
            items.append((idx, sub_mp3, starts[idx - 1], actual_dur))

    wrapped = wrap_chunks_concurrently(items, max_workers=max_workers)
    for seg in wrapped:
        seg["sub_index"] = seg.pop("part_num")
        seg["md_path"] = seg["mp3_path"].rsplit(".", 1)[0] + ".md"

    return {
        "source_mp3": mp3_path,
        "total_duration": round(total_dur, 2),
        "parts": parts,
        "segments": wrapped,
    }


def main():
    parser = argparse.ArgumentParser(description="Segment audio and wrap into 1fps MP4s for ec2-stt")
    parser.add_argument("audio", nargs="?", help="Input audio file path")
    parser.add_argument("--work-dir", help="Directory to save segments")
    parser.add_argument("--prefix", help="Filename prefix (e.g. 1106 전회2)")
    parser.add_argument("--segment-seconds", type=int, default=50, help="Target segment length in seconds (default: 50)")
    parser.add_argument("--window-seconds", type=int, default=12, help="Silence search half-window in seconds; 0 disables silence-aware splitting (default: 12)")
    parser.add_argument("--max-workers", type=int, default=4, help="Max parallel ffmpeg wrapping workers")
    parser.add_argument("--resplit", help="Resplit a single failing MP3 chunk into equal subchunks")
    parser.add_argument("--parts", type=int, default=3, help="Number of subchunks for --resplit (default: 3)")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")

    args = parser.parse_args()

    if args.resplit:
        result = resplit_chunk(args.resplit, parts=args.parts, max_workers=args.max_workers)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Resplit {result['source_mp3']} into {len(result['segments'])} subchunks.")
        return

    if not args.audio or not args.work_dir or not args.prefix:
        parser.error("audio, --work-dir, and --prefix are required unless --resplit is used")

    result = prepare_segments(
        audio_path=args.audio,
        work_dir=args.work_dir,
        prefix=args.prefix,
        segment_seconds=args.segment_seconds,
        window_seconds=args.window_seconds,
        max_workers=args.max_workers,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Successfully prepared {result['num_segments']} segments in {result['work_dir']}.")
        print(f"Total duration: {result['total_duration']}s, target: {result['segment_seconds']}s (+/-{result['window_seconds']}s)")


if __name__ == "__main__":
    main()
