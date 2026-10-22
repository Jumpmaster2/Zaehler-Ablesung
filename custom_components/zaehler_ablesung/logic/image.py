"""Rotate, crop and brighten the camera picture so the AI only sees the display."""

from __future__ import annotations

import io

MAX_ROTATION = 180
EXPOSURE_RANGE = (10, 400)


def rotation(value: str | float | None) -> float:
    """Clockwise angle in -180..180; older versions stored "0", "90", "180" or "270"."""
    try:
        degrees = float(value or 0)
    except (TypeError, ValueError):
        return 0.0
    degrees = degrees % 360
    if degrees > MAX_ROTATION:
        degrees -= 360
    return degrees


def crop_after_rotation(
    left: float, top: float, right: float, bottom: float, rotate: str | float
) -> tuple[float, float, float, float]:
    """Crop of older versions (cropped, then turned by a right angle) for the turned picture."""
    degrees = rotation(rotate)
    if degrees == 90:
        return 100 - bottom, left, 100 - top, right
    if degrees == 180:
        return 100 - right, 100 - bottom, 100 - left, 100 - top
    if degrees == -90:
        return top, 100 - right, bottom, 100 - left
    return left, top, right, bottom


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
    left: float,
    top: float,
    right: float,
    bottom: float,
    rotate: str | float = 0,
    exposure: float = 100,
    enhance: bool = False,
) -> bool:
    return (
        bool(enhance)
        or rotation(rotate) != 0
        or float(exposure) != 100
        or crop_box(100, 100, left, top, right, bottom) is not None
    )


def enhanced(image):
    """Grey picture with even lighting and full contrast.

    A light next to the lens leaves a bright spot on the display glass and dark
    corners. Dividing by a strongly blurred copy evens out the lighting, so the
    segments stand out the same everywhere; then the contrast is stretched.
    """
    from PIL import ImageFilter, ImageMath, ImageOps

    grey = image.convert("L").filter(ImageFilter.MedianFilter(3))
    # much wider than a segment, so the blurred copy only holds the lighting
    background = grey.filter(ImageFilter.GaussianBlur(max(4, max(grey.size) / 25)))
    even = ImageMath.lambda_eval(
        lambda a: a["convert"](a["grey"] * 128 / (a["background"] + 4), "L"),
        grey=grey,
        background=background,
    )
    return ImageOps.autocontrast(even, cutoff=1).convert("RGB")


def process(
    content: bytes,
    left: float = 0,
    top: float = 0,
    right: float = 100,
    bottom: float = 100,
    rotate: str | float = 0,
    exposure: float = 100,
    enhance: bool = False,
) -> bytes:
    """Rotated, cropped, brightened and enhanced JPEG; the original when nothing is to do or it cannot be decoded."""
    if not needs_processing(left, top, right, bottom, rotate, exposure, enhance):
        return content
    from PIL import Image, ImageEnhance, UnidentifiedImageError

    try:
        image = Image.open(io.BytesIO(content))
        image.load()
    except (UnidentifiedImageError, OSError):
        return content
    image = image.convert("RGB")
    # rotate first, so the crop is drawn on the straight picture
    degrees = rotation(rotate)
    if degrees:
        # clockwise like a camera that is mounted turned to the right; right angles stay sharp
        transpose = {
            90: Image.Transpose.ROTATE_270,
            180: Image.Transpose.ROTATE_180,
            -90: Image.Transpose.ROTATE_90,
        }.get(degrees)
        if transpose is not None:
            image = image.transpose(transpose)
        else:
            image = image.rotate(-degrees, resample=Image.Resampling.BICUBIC, expand=True)
    box = crop_box(image.width, image.height, left, top, right, bottom)
    if box:
        image = image.crop(box)
    low, high = EXPOSURE_RANGE
    factor = max(low, min(high, float(exposure))) / 100
    if factor != 1:
        image = ImageEnhance.Brightness(image).enhance(factor)
    if enhance:
        image = enhanced(image)
    out = io.BytesIO()
    image.save(out, format="JPEG", quality=92)
    return out.getvalue()


def thumbnail(content: bytes, size: int = 640) -> bytes:
    """Smaller JPEG for an overview; the original when it is small or cannot be decoded."""
    from PIL import Image, UnidentifiedImageError

    try:
        image = Image.open(io.BytesIO(content))
        image.load()
    except (UnidentifiedImageError, OSError):
        return content
    if max(image.size) <= size:
        return content
    image.thumbnail((size, size))
    out = io.BytesIO()
    image.convert("RGB").save(out, format="JPEG", quality=80)
    return out.getvalue()
