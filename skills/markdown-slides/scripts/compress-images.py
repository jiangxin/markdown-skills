#!/usr/bin/env python3
"""Compress PNG/JPEG images while keeping format and aspect ratio.

Longest side is capped at 1024px (no upscaling). Encoded size is capped at
900KB. JPEG uses quality search; PNG uses optimize / palette / further
downscale if needed.
"""

from __future__ import annotations

import argparse
import io
import shutil
import sys
import tempfile
from pathlib import Path

import config

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.stderr.write("Need Pillow: python3 -m pip install Pillow\n")
    sys.exit(1)

DEFAULT_MAX_SIDE = 1024
DEFAULT_MAX_BYTES = 900 * 1024
MIN_SIDE = 64
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
JPEG_QUALITY_MAX = 95
JPEG_QUALITY_MIN = 20


def parse_size(text: str) -> int:
    raw = text.strip().upper().replace(" ", "")
    for suffix, mul in (("KB", 1024), ("K", 1024), ("MB", 1024 * 1024), ("M", 1024 * 1024), ("B", 1)):
        if raw.endswith(suffix):
            return int(float(raw[: -len(suffix)]) * mul)
    return int(raw)


def human_bytes(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.1f}MB"
    if n >= 1024:
        return f"{n / 1024:.1f}KB"
    return f"{n}B"


def fit_size(width: int, height: int, max_side: int) -> tuple[int, int]:
    longest = max(width, height)
    if longest <= max_side:
        return width, height
    scale = max_side / longest
    return max(1, round(width * scale)), max(1, round(height * scale))


def format_from_image(image: Image.Image, path: Path) -> str:
    fmt = (image.format or "").upper()
    if fmt == "JPG":
        fmt = "JPEG"
    if fmt in {"PNG", "JPEG"}:
        return fmt
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "PNG"
    if suffix in {".jpg", ".jpeg"}:
        return "JPEG"
    raise ValueError(f"unsupported format: {path}")


def drop_unused_alpha(image: Image.Image) -> Image.Image:
    if image.mode != "RGBA":
        return image
    minimum, maximum = image.getchannel("A").getextrema()
    if minimum == 255 and maximum == 255:
        return image.convert("RGB")
    return image


def resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    if image.size == size:
        return image
    return image.resize(size, Image.Resampling.LANCZOS)


def encode_png(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=True, compress_level=9)
    return buf.getvalue()


def encode_jpeg(image: Image.Image, quality: int) -> bytes:
    to_save = image
    if to_save.mode not in {"RGB", "L"}:
        to_save = to_save.convert("RGB")
    buf = io.BytesIO()
    to_save.save(
        buf,
        format="JPEG",
        quality=quality,
        optimize=True,
        progressive=True,
        subsampling="4:2:0",
    )
    return buf.getvalue()


def jpeg_under_limit(image: Image.Image, max_bytes: int) -> bytes:
    best: bytes | None = None
    low, high = JPEG_QUALITY_MIN, JPEG_QUALITY_MAX
    while low <= high:
        mid = (low + high) // 2
        data = encode_jpeg(image, mid)
        if len(data) <= max_bytes:
            best = data
            low = mid + 1
        else:
            high = mid - 1
    if best is not None:
        return best
    return encode_jpeg(image, JPEG_QUALITY_MIN)


def png_candidates(image: Image.Image) -> list[Image.Image]:
    base = drop_unused_alpha(image)
    out = [base]
    if base.mode not in {"P"}:
        colors = 256 if base.mode != "RGBA" else 255
        try:
            out.append(base.quantize(colors=colors, method=Image.Quantize.MEDIANCUT))
        except ValueError:
            pass
        try:
            out.append(base.quantize(colors=max(16, colors // 2), method=Image.Quantize.MEDIANCUT))
        except ValueError:
            pass
    return out


def png_under_limit(image: Image.Image, max_bytes: int) -> bytes:
    best: bytes | None = None
    for candidate in png_candidates(image):
        data = encode_png(candidate)
        if best is None or len(data) < len(best):
            best = data
        if len(data) <= max_bytes:
            return data
    assert best is not None
    return best


def encode_under_limit(image: Image.Image, fmt: str, max_bytes: int) -> bytes:
    if fmt == "JPEG":
        return jpeg_under_limit(image, max_bytes)
    if fmt == "PNG":
        return png_under_limit(image, max_bytes)
    raise ValueError(f"unsupported format: {fmt}")


def compress_image(image: Image.Image, fmt: str, max_side: int, max_bytes: int) -> tuple[bytes, tuple[int, int]]:
    orig_w, orig_h = image.size
    longest = max(orig_w, orig_h)
    side = min(longest, max_side)
    best_data: bytes | None = None
    best_size = image.size

    while side >= MIN_SIDE:
        target = fit_size(orig_w, orig_h, side)
        data = encode_under_limit(resize(image, target), fmt, max_bytes)
        if best_data is None or len(data) < len(best_data):
            best_data = data
            best_size = target
        if len(data) <= max_bytes:
            return data, target
        next_side = max(MIN_SIDE, int(side * 0.85))
        if next_side >= side:
            next_side = side - 1
        side = next_side

    assert best_data is not None
    return best_data, best_size


def collect_inputs(paths: list[Path], recursive: bool) -> list[Path]:
    found: list[Path] = []
    for path in paths:
        if path.is_file():
            found.append(path)
            continue
        if not path.is_dir():
            raise FileNotFoundError(path)
        globber = path.rglob if recursive else path.glob
        found.extend(sorted(p for p in globber("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES))
    return found


def output_path_for(src: Path, output_dir: Path | None) -> Path:
    if output_dir is None:
        return src
    return output_dir / src.name


def atomic_write(dest: Path, data: bytes) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=dest.parent, prefix=f".{dest.name}.", suffix=dest.suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    tmp_path.replace(dest)


def process_file(
    src: Path,
    dest: Path,
    max_side: int,
    max_bytes: int,
    dry_run: bool,
) -> str:
    orig_bytes = src.stat().st_size
    with Image.open(src) as opened:
        image = ImageOps.exif_transpose(opened)
        image.load()
        fmt = format_from_image(opened, src)
        orig_size = image.size

        already_ok = max(orig_size) <= max_side and orig_bytes <= max_bytes
        if already_ok:
            summary = f"{src}  {orig_size[0]}x{orig_size[1]}  {human_bytes(orig_bytes)}"
            if dest == src:
                return f"skip  {summary}"
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
            action = "would copy" if dry_run else "copied"
            return f"{action}  {summary} -> {dest}"

        data, new_size = compress_image(image, fmt, max_side, max_bytes)

    over = "" if len(data) <= max_bytes else "  WARN still over limit"
    action = "would write" if dry_run else "wrote"
    if not dry_run:
        atomic_write(dest, data)
    shown_dest = dest if dest != src else src
    return (
        f"{action}  {src}  {orig_size[0]}x{orig_size[1]} {human_bytes(orig_bytes)}"
        f" -> {shown_dest}  {new_size[0]}x{new_size[1]} {human_bytes(len(data))}{over}"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="image files or directories (default: the deck root)",
    )
    parser.add_argument(
        "--deck-root",
        help="deck directory (--deck-root, else DECK_ROOT, else the skill root)",
    )
    parser.add_argument("--max-side", type=int, default=DEFAULT_MAX_SIDE, help="longest side in pixels")
    parser.add_argument(
        "--max-bytes",
        type=parse_size,
        default=DEFAULT_MAX_BYTES,
        help="max encoded size, e.g. 900KB",
    )
    parser.add_argument("-o", "--output-dir", type=Path, help="write here instead of overwriting")
    parser.add_argument("-r", "--recursive", action="store_true", help="recurse into directories")
    parser.add_argument("-n", "--dry-run", action="store_true", help="report only, do not write")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    paths = args.paths or [config.deck_root()]
    try:
        inputs = collect_inputs(paths, args.recursive)
    except FileNotFoundError as exc:
        sys.stderr.write(f"not found: {exc}\n")
        return 1

    if not inputs:
        sys.stderr.write("no PNG/JPEG files found\n")
        return 1

    failed = 0
    for src in inputs:
        if src.suffix.lower() not in IMAGE_SUFFIXES:
            print(f"skip  {src}  unsupported suffix")
            continue
        dest = output_path_for(src, args.output_dir)
        try:
            print(process_file(src, dest, args.max_side, args.max_bytes, args.dry_run))
        except Exception as exc:  # noqa: BLE001 — report per-file and continue
            failed += 1
            sys.stderr.write(f"fail  {src}  {exc}\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
