"""Intensity utilities that do not alter MRI spatial geometry."""

import numpy as np


def normalize_intensity(volume: np.ndarray, lower_percentile: float = 1.0, upper_percentile: float = 99.0) -> np.ndarray:
    """Clip outliers and scale intensities to [0, 1] without resizing or changing spacing."""
    array = np.asarray(volume, dtype=np.float32)
    if array.ndim != 3 or array.size == 0:
        raise ValueError("Expected a non-empty 3D volume.")
    if not (0 <= lower_percentile < upper_percentile <= 100):
        raise ValueError("Percentiles must satisfy 0 <= lower < upper <= 100.")
    if not np.isfinite(array).all():
        raise ValueError("Volume contains NaN or infinite values.")
    low, high = np.percentile(array, [lower_percentile, upper_percentile])
    if high <= low:
        return np.zeros_like(array, dtype=np.float32)
    clipped = np.clip(array, low, high)
    return ((clipped - low) / (high - low)).astype(np.float32)
