"""Crop and rotate the camera picture so the AI only sees the display."""

from __future__ import annotations

import io

ROTATIONS = ["0", "90", "180", "270"]


def crop_box(
    width: int, height: int, left: float, top: float, right: float, bottom: float
) -> tuple[int, int, int, int] | None:
    """Pixel box for edges in percent; None for the whole picture or an invalid box."""
    left, right = sorted((max(0.0, min(100.0, left)), max(0.0, min(100.0, right))))
    top, bottom = sorted((max(0.0, min(100.0, top)), max(0.0, min(100.0, bottom))))
    if right - left < 1 or bottom - top < 1:
        return None
    if left <= 0 and top <= 0 and right >= 100 and bottom >= 100:
        return None
    return (
        round(width * left / 100),
        round(height * top / 100),
        round(width * right / 100),
        round(height * bottom / 100),
    )


def needs_processing(
    left: float, top: float, right: float, bottom: float, rotate: str | int
) -> bool:
    return str(rotate) != "0" or crop_box(100, 100, left, top, right, bottom) is not None


def process(
    content: bytes,
    left: float = 0,
    top: float = 0,
    right: float = 100,
    bottom: float = 100,
    rotate: str | int = "0",
) -> bytes:
    """Cropped and rotated JPEG; the original when nothing is to do or it cannot be decoded."""
    if not needs_processing(left, top, right, bottom, rotate):
        return content
    from PIL import Image, UnidentifiedImageError

    try:
        image = Image.open(io.BytesIO(content))
        image.load()
    except (UnidentifiedImageError, OSError):
        return content
    box = crop_box(image.width, image.height, left, top, right, bottom)
    if box:
        image = image.crop(box)
    degrees = int(str(rotate)) % 360
    if degrees:
        # clockwise like a camera that is mounted turned to the right
        image = image.rotate(-degrees, expand=True)
    out = io.BytesIO()
    image.convert("RGB").save(out, format="JPEG", quality=92)
    return out.getvalue()
