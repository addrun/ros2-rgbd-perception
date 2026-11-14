# SPDX-License-Identifier: AGPL-3.0-only
import numpy as np
import pytest
from rgbd_perception.geometry import Intrinsics, depth_in_metres, estimate_target

CAMERA = Intrinsics(600, 600, 320, 240)


def test_millimetres_and_float_metres_agree():
    mm = np.full((480, 640), 1500, np.uint16)
    metres = np.full((480, 640), 1.5, np.float32)
    assert np.allclose(depth_in_metres(mm, "16UC1"), depth_in_metres(metres, "32FC1"))
    p, axis, valid = estimate_target(depth_in_metres(mm, "16UC1"), [180, 180, 460, 300], CAMERA)
    assert p == pytest.approx([0, 0, 1.5])
    assert valid and abs(axis[0]) > .99


def test_original_image_box_center_is_not_rescaled_twice():
    depth = np.full((480, 640), 2, np.float32)
    p, _, _ = estimate_target(depth, [400, 200, 600, 280], CAMERA)
    assert p == pytest.approx([.6, 0, 2])


def test_invalid_depth_and_outside_boxes_are_skipped():
    depth = np.full((480, 640), np.nan, np.float32)
    assert estimate_target(depth, [180, 180, 460, 300], CAMERA) is None
    assert estimate_target(np.ones_like(depth), [700, 0, 800, 100], CAMERA) is None


def test_isotropic_roi_does_not_claim_an_orientation():
    depth = np.full((480, 640), 1.5, np.float32)
    _, axis, valid = estimate_target(depth, [200, 120, 440, 360], CAMERA)
    assert not valid and np.all(axis == 0)


def test_invalid_metadata_is_rejected():
    with pytest.raises(ValueError):
        Intrinsics(0, 600, 320, 240)
    with pytest.raises(ValueError):
        depth_in_metres(np.ones((4, 4), np.uint16), "32FC1")
    with pytest.raises(ValueError):
        depth_in_metres(np.ones((4, 4), np.float32), "mono8")
