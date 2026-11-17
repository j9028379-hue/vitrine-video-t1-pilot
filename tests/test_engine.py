from __future__ import annotations

import numpy as np

from engine.t1_engine import easing, transition_frame, zoom_frame


def test_easing_is_monotonic_and_bounded() -> None:
    values = [easing(i / 100) for i in range(101)]
    assert values[0] == 0.0 and values[-1] == 1.0
    assert values == sorted(values)
    assert all(0.0 <= value <= 1.0 for value in values)


def test_zoom_keeps_render_dimensions() -> None:
    image = np.zeros((1280, 720, 3), dtype=np.uint8)
    result = zoom_frame(image, 1.25)
    assert result.shape == image.shape


def test_transition_preserves_shape_and_dtype() -> None:
    old = np.zeros((1280, 720, 3), dtype=np.uint8)
    new = np.full((1280, 720, 3), 255, dtype=np.uint8)
    result = transition_frame(old, new, "TR05", 2, 6)
    assert result.shape == new.shape
    assert result.dtype == np.uint8
    assert 0 < int(result[0, 0, 0]) < 255
