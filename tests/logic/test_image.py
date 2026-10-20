"""Crop and rotate the picture."""

from __future__ import annotations

import io

import pytest
from logic.image import crop_box, needs_processing, process

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


def test_process() -> None:
    original = _jpeg(1000, 800)
    assert process(original) is original
    cropped = Image.open(io.BytesIO(process(original, 10, 50, 60, 100)))
    assert cropped.size == (500, 400)
    turned = Image.open(io.BytesIO(process(original, 10, 50, 60, 100, "90")))
    assert turned.size == (400, 500)
    # not a picture: unchanged
    assert process(b"no jpeg", 10, 10, 50, 50) == b"no jpeg"
