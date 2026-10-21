"""Crop, rotate and brighten the picture."""

from __future__ import annotations

import io

import pytest
from logic.image import crop_after_rotation, crop_box, needs_processing, process, rotation

Image = pytest.importorskip("PIL.Image")


def _jpeg(width: int, height: int) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (width, height), (200, 10, 10)).save(out, format="JPEG")
    return out.getvalue()


def test_crop_box() -> None:
    assert crop_box(1000, 800, 0, 0, 100, 100) is None
    assert crop_box(1000, 800, 10, 50, 60, 100) == (100, 400, 600, 800)
    # swapped edges are sorted, out of range values are clamped
    assert crop_box(1000, 800, 60, 100, 10, 50) == (100, 400, 600, 800)
    assert crop_box(1000, 800, -5, 0, 50, 120) == (0, 0, 500, 800)
    # too small: whole picture
    assert crop_box(1000, 800, 10, 10, 10.5, 50) is None


def test_needs_processing() -> None:
    assert not needs_processing(0, 0, 100, 100, "0")
    assert needs_processing(0, 0, 100, 100, "90")
    assert needs_processing(10, 0, 100, 100, 0)
    assert needs_processing(0, 0, 100, 100, 2.5)
    assert needs_processing(0, 0, 100, 100, 0, 120)
    assert not needs_processing(0, 0, 100, 100, "0", 100)


def test_rotation() -> None:
    # stored values of older versions
    assert rotation("0") == 0
    assert rotation("90") == 90
    assert rotation("180") == 180
    assert rotation("270") == -90
    assert rotation(None) == 0
    assert rotation("x") == 0
    assert rotation(-12.5) == -12.5
    assert rotation(-180) == 180


def test_process() -> None:
    original = _jpeg(1000, 800)
    assert process(original) is original
    cropped = Image.open(io.BytesIO(process(original, 10, 50, 60, 100)))
    assert cropped.size == (500, 400)
    turned = Image.open(io.BytesIO(process(original, 10, 50, 60, 100, "90")))
    assert turned.size == (400, 500)
    turned = Image.open(io.BytesIO(process(original, rotate=-90)))
    assert turned.size == (800, 1000)
    # a few degrees: the picture grows so nothing is cut off
    tilted = Image.open(io.BytesIO(process(original, rotate=5)))
    assert tilted.width > 1000 and tilted.height > 800
    darker = Image.open(io.BytesIO(process(original, exposure=50)))
    brighter = Image.open(io.BytesIO(process(original, exposure=200)))
    red = Image.open(io.BytesIO(original)).getpixel((500, 400))[0]
    assert darker.getpixel((500, 400))[0] < red < brighter.getpixel((500, 400))[0]
    # not a picture: unchanged
    assert process(b"no jpeg", 10, 10, 50, 50) == b"no jpeg"


def _quarters() -> Image.Image:
    """Picture with a different colour in each quarter."""
    image = Image.new("RGB", (1000, 800))
    colours = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    for i, colour in enumerate(colours):
        x, y = (i % 2) * 500, (i // 2) * 400
        image.paste(colour, (x, y, x + 500, y + 400))
    return image


def _png(image: Image.Image) -> bytes:
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()


def test_rotate_before_crop() -> None:
    # turned clockwise the left half of the picture is the top half: the crop takes it
    image = Image.open(io.BytesIO(process(_png(_quarters()), 0, 0, 100, 50, "90")))
    assert image.size == (800, 500)
    # top left was the bottom left (blue), top right the top left (red)
    assert image.getpixel((100, 100))[2] > 200
    assert image.getpixel((700, 100))[0] > 200 and image.getpixel((700, 100))[1] < 50


@pytest.mark.parametrize("rotate", ["90", "180", "270"])
def test_crop_after_rotation(rotate: str) -> None:
    # older versions cropped first and turned then; the converted crop gives the same picture
    source = _quarters()
    crop = (10, 20, 70, 90)
    old = source.crop(crop_box(1000, 800, *crop)).rotate(-int(rotate), expand=True)
    new = Image.open(io.BytesIO(process(_png(source), *crop_after_rotation(*crop, rotate), rotate)))
    assert new.size == old.size
    for x, y in ((5, 5), (new.width - 5, 5), (5, new.height - 5), (new.width - 5, new.height - 5)):
        assert all(
            abs(a - b) < 40 for a, b in zip(new.getpixel((x, y)), old.getpixel((x, y)), strict=True)
        )
    assert crop_after_rotation(*crop, 0) == crop
