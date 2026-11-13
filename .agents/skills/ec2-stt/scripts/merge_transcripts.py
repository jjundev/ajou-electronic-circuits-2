#!/usr/bin/env python3
"""
Merge segmented STT markdown files into a master transcript for ec2-stt.

Supports manifest-driven merging (--manifest ec2_stt_segments.json):
- Aggregates recovery subchunks (e.g. _part16_1.md, _part16a.md) under their parent part.
- Computes accurate 5-minute ## Part NN headers and MM:SS offsets from start_time.
- Validates that every manifest part has non-empty text before writing or deleting files.
- Removes intermediate chunk files and empty _temp_* working directories.
"""

import argparse
from collections import defaultdict
import json
import os
import re
import sys
import unicodedata


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def natural_sort_key(text: str) -> list[tuple[int, int | str]]:
    """Sort key that orders numeric tokens numerically (e.g. _2 before _10)."""
    parts = re.split(r"(\d+)", text)
    return [(0, int(p)) if p.isdigit() else (1, p) for p in parts if p]


def read_part_body(part_path: str, offset_seconds: int, timestamps: bool) -> str:
    """Read a chunk markdown file, stripping its leading # header and shifting timestamps."""
    timestamp_pattern = re.compile(r"^(\d{1,2}):(\d{2})$")
    with open(part_path, "r", encoding="utf-8") as pf:
        lines = pf.readlines()

    content_lines: list[str] = []
    skip_header = True
    for line in lines:
        line_str = line.strip()
        if skip_header and (line_str.startswith("#") or not line_str):
            continue
        skip_header = False

        tm = timestamp_pattern.match(line_str)
        if tm:
            if timestamps:
                mins = int(tm.group(1))
                secs = int(tm.group(2))
                total_secs = offset_seconds + (mins * 60) + secs
                content_lines.append(f"{total_secs // 60:02d}:{total_secs % 60:02d}\n")
            continue
        content_lines.append(line)

    return "".join(content_lines).strip()


def discover_part_files(target_dir: str, prefix: str) -> dict[int, list[tuple[str, str]]]:
    """Group part and recovery subchunk markdown files by parent part_num."""
    escaped_prefix = re.escape(nfc(prefix)) if prefix else ""
    pattern = re.compile(
        rf"^{escaped_prefix}.*?part(\d+)([_a-z0-9]*)\.md$"
        if escaped_prefix
        else r"^.*?part(\d+)([_a-z0-9]*)\.md$"
    )
    grouped: dict[int, list[tuple[str, str]]] = defaultdict(list)
    for f in os.listdir(target_dir):
        m = pattern.match(nfc(f))
        if m:
            grouped[int(m.group(1))].append((m.group(2), os.path.join(target_dir, f)))

    for part_num, entries in grouped.items():
        exact = [e for e in entries if e[0] == ""]
        subs = [e for e in entries if e[0] != ""]
        subs.sort(key=lambda e: natural_sort_key(e[0]))
        # Prefer exact partNN.md if present; otherwise concatenate sorted subchunks
        grouped[part_num] = exact if exact else subs

    return dict(sorted(grouped.items()))


def load_manifest(manifest_path: str) -> dict[int, dict]:
    """Load segments manifest keyed by part_num."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {int(seg["part_num"]): seg for seg in data.get("segments", [])}


def cleanup_intermediates(target_dir: str, prefix: str, output_path: str) -> None:
    """Remove intermediate chunk files and empty _temp_* directory."""
    cleaned_count = 0
    output_abs = os.path.abspath(output_path)
    prefix_nfc = nfc(prefix)

    for f in os.listdir(target_dir):
        fn = nfc(f)
        is_chunk_md = bool(re.search(r"_part\d+.*\.md$", fn))
        is_chunk_mp3 = bool(re.search(r"_part\d+.*\.mp3$", fn))
        is_chunk_mp4 = bool(re.search(r"_part\d+.*_temp\.mp4$", fn))

        matches_prefix = fn.startswith(prefix_nfc) if prefix_nfc else True
        if matches_prefix and (is_chunk_md or is_chunk_mp3 or is_chunk_mp4):
            fpath = os.path.join(target_dir, f)
            if os.path.abspath(fpath) == output_abs:
                continue
            try:
                os.remove(fpath)
                cleaned_count += 1
            except OSError as e:
                print(f"Warning: Failed to delete intermediate file {f}: {e}", file=sys.stderr)

    print(f"Cleaned up {cleaned_count} intermediate chunk files.")

    if os.path.basename(target_dir).startswith("_temp_") and not os.listdir(target_dir):
        try:
            os.rmdir(target_dir)
            print(f"Removed empty temporary directory: {target_dir}")
        except OSError as e:
            print(f"Warning: Failed to remove temporary directory {target_dir}: {e}", file=sys.stderr)


def merge_transcripts(
    target_dir: str,
    prefix: str = "",
    segment_seconds: int = 50,
    group_parts: int = 2,
    keep_parts: bool = False,
    output_file: str = "",
    out_file: str = "",
    timestamps: bool = False,
    speakers: list[str] | str | None = None,
    manifest_path: str = "",
    strict: bool = True,
) -> str:
    target_dir = os.path.abspath(target_dir)
    output_path_candidate = output_file or out_file

    if not os.path.isdir(target_dir):
        print(f"Error: Target directory does not exist: {target_dir}", file=sys.stderr)
        return ""

    grouped_files = discover_part_files(target_dir, prefix)
    if not grouped_files:
        print(f"Error: No matching part markdown files found in {target_dir}", file=sys.stderr)
        return ""

    manifest = load_manifest(manifest_path) if manifest_path else {}

    if manifest and strict:
        missing = [
            pnum for pnum in sorted(manifest)
            if pnum not in grouped_files
        ]
        if missing:
            print(
                f"Error: Missing transcript files for manifest parts: {missing}. Aborting merge without cleanup.",
                file=sys.stderr,
            )
            sys.exit(1)

    if output_path_candidate:
        output_path = os.path.abspath(output_path_candidate)
    elif prefix:
        output_path = os.path.join(target_dir, f"{prefix}.md")
    else:
        output_path = os.path.join(target_dir, "transcript.md")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    full_content = [f"# {prefix or os.path.basename(target_dir)} 전체 오디오 전사본\n\n"]
    current_header_idx = 0
    empty_parts: list[int] = []

    part_order = sorted(manifest) if manifest else sorted(grouped_files)
    for part_num in part_order:
        if part_num not in grouped_files:
            continue

        if part_num in manifest and "start_time" in manifest[part_num]:
            start_time = float(manifest[part_num]["start_time"])
            offset_seconds = int(round(start_time))
            header_num = int(start_time // 300) + 1
            header_start_min = ((header_num - 1) * 300) // 60
        else:
            offset_seconds = (part_num - 1) * segment_seconds
            header_num = ((part_num - 1) // group_parts) + 1 if group_parts > 1 else part_num
            header_start_min = (((header_num - 1) * group_parts) * segment_seconds) // 60

        if header_num != current_header_idx:
            current_header_idx = header_num
            if timestamps:
                full_content.append(f"## Part {header_num:02d} ({header_start_min:02d}:00 ~ )\n\n")
            else:
                full_content.append(f"## Part {header_num:02d}\n\n")

        sub_bodies = [
            read_part_body(fpath, offset_seconds, timestamps)
            for _, fpath in grouped_files[part_num]
        ]
        body = "\n\n".join(b for b in sub_bodies if b)
        if not body:
            empty_parts.append(part_num)
        else:
            full_content.append(body + "\n\n")

    if manifest and strict and empty_parts:
        print(
            f"Error: Empty transcript body for manifest parts: {empty_parts}. Aborting merge without cleanup.",
            file=sys.stderr,
        )
        sys.exit(1)

    raw_text = "".join(full_content)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", raw_text).strip() + "\n"

    with open(output_path, "w", encoding="utf-8") as out:
        out.write(cleaned_text)

    print(f"Master transcript successfully created: {output_path}")

    if speakers:
        if isinstance(speakers, str):
            speaker_list = [s.strip() for s in speakers.split(",") if s.strip()]
        else:
            speaker_list = [s.strip() for s in speakers if s.strip()]

        allowed = set(speaker_list) | {"화자?"}
        label_pattern = re.compile(r"^\*\*(.+?):\*\*", re.MULTILINE)
        found = set(label_pattern.findall(cleaned_text))
        unknown = sorted(found - allowed)
        if unknown:
            print(
                "Warning: speaker labels not in roster: " + ", ".join(repr(u) for u in unknown),
                file=sys.stderr,
            )

    if not keep_parts and os.path.isfile(output_path) and os.path.getsize(output_path) > 0:
        cleanup_intermediates(target_dir, prefix, output_path)

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Merge segmented transcripts for ec2-stt")
    parser.add_argument("--dir", required=True, help="Directory containing part files")
    parser.add_argument("--prefix", default="", help="Prefix of the part files (e.g. 1002 전회2)")
    parser.add_argument("--out", default="", help="Final output file path")
    parser.add_argument("--manifest", default="", help="Path to ec2_stt_segments.json from prepare_segments.py")
    parser.add_argument("--segment-seconds", type=int, default=50, help="Fallback segment length in seconds when --manifest is omitted (default: 50)")
    parser.add_argument("--group-parts", type=int, default=2, help="Fallback chunk grouping when --manifest is omitted (default: 2)")
    parser.add_argument("--keep-parts", action="store_true", help="Preserve intermediate part files")
    parser.add_argument("--no-strict", action="store_true", help="Allow merging even if manifest parts are missing/empty")
    parser.add_argument("--timestamps", action="store_true", help="Include continuous MM:SS timestamps")
    parser.add_argument("--speakers", default="", help="Comma-separated allowed speaker labels")

    args = parser.parse_args()
    merge_transcripts(
        target_dir=args.dir,
        prefix=args.prefix,
        segment_seconds=args.segment_seconds,
        group_parts=args.group_parts,
        keep_parts=args.keep_parts,
        output_file=args.out,
        timestamps=args.timestamps,
        speakers=args.speakers,
        manifest_path=args.manifest,
        strict=not args.no_strict,
    )


if __name__ == "__main__":
    main()
