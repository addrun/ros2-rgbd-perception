# SPDX-License-Identifier: AGPL-3.0-only
"""Metric geometry for depth already registered to an undistorted colour image."""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Intrinsics:
    fx: float
    fy: float
    cx: float
    cy: float

    def __post_init__(self):
        if not np.isfinite([self.fx, self.fy, self.cx, self.cy]).all() or min(self.fx, self.fy) <= 0:
            raise ValueError("invalid camera intrinsics")


def depth_in_metres(depth, encoding):
    if encoding == "16UC1":
        if depth.dtype != np.uint16:
            raise ValueError("16UC1 depth must have uint16 data")
        return depth.astype(np.float32) * .001
    if encoding == "32FC1":
        if depth.dtype != np.float32:
            raise ValueError("32FC1 depth must have float32 data")
        return depth.copy()
    raise ValueError(f"unsupported depth encoding: {encoding}")


def estimate_target(depth_m, bbox, camera, min_depth=.1, max_depth=10.):
    """Median ROI depth, backprojection and an optional unsigned PCA axis.

    bbox is already in original-image pixels. No letterbox scaling happens here.
    Returns None when no valid target depth is available.
    """
    if depth_m.ndim != 2:
        raise ValueError("depth must be a single-channel image")
    if not (np.isfinite([min_depth, max_depth]).all() and 0 < min_depth < max_depth):
        raise ValueError("invalid depth limits")
    b = np.asarray(bbox, dtype=float)
    if b.shape != (4,) or not np.isfinite(b).all():
        raise ValueError("bbox must contain four finite numbers")
    h, w = depth_m.shape
    x1, y1, x2, y2 = b
    if x2 <= x1 or y2 <= y1 or x2 <= 0 or y2 <= 0 or x1 >= w or y1 >= h:
        return None
    x1, x2 = np.clip([x1, x2], 0, w)
    y1, y2 = np.clip([y1, y2], 0, h)
    # Ignore a narrow boundary band to reduce background pixels in the box.
    dx, dy = .1 * (x2-x1), .1 * (y2-y1)
    left, right = int(np.floor(x1+dx)), int(np.ceil(x2-dx))
    top, bottom = int(np.floor(y1+dy)), int(np.ceil(y2-dy))
    roi = depth_m[top:bottom, left:right]
    valid = np.isfinite(roi) & (roi >= min_depth) & (roi <= max_depth)
    if np.count_nonzero(valid) < 10:
        return None
    z = float(np.median(roi[valid]))
    u, v = (x1+x2)/2, (y1+y2)/2
    position = np.array([(u-camera.cx)*z/camera.fx, (v-camera.cy)*z/camera.fy, z])
    yy, xx = np.nonzero(valid & (np.abs(roi-z) <= max(.03, .05*z)))
    step = max(1, int(np.ceil(len(xx)/2000)))
    xx, yy = xx[::step], yy[::step]
    axis = np.zeros(3); axis_valid = False
    if len(xx) >= 10:
        zz = roi[yy, xx]
        points = np.column_stack(((xx+left-camera.cx)*zz/camera.fx,
                                  (yy+top-camera.cy)*zz/camera.fy, zz))
        values, vectors = np.linalg.eigh(np.cov(points, rowvar=False))
        # Near-square or isotropic crops do not have a reliable principal line.
        axis_valid = bool(values[-1] > 1e-10 and values[-1] > 1.5*values[-2])
        if axis_valid:
            axis = vectors[:, -1]
            # Deterministic sign for an otherwise unsigned line, not a heading.
            first = np.flatnonzero(np.abs(axis) > 1e-8)[0]
            if axis[first] < 0:
                axis = -axis
    return position, axis, axis_valid
