"""Orthogonal slice and 3D intensity visualization for MRI volumes."""

from __future__ import annotations

import math

import numpy as np
import plotly.graph_objects as go

from src.volume_io import MRIVolume


def make_slice_figure(volume: MRIVolume, plane: str, index: int) -> go.Figure:
    """Create an axial, coronal, or sagittal slice view."""
    planes = {
        "axial": (0, volume.data.shape[0], lambda i: volume.data[i, :, :]),
        "coronal": (1, volume.data.shape[1], lambda i: volume.data[:, i, :]),
        "sagittal": (2, volume.data.shape[2], lambda i: volume.data[:, :, i]),
    }
    if plane not in planes:
        raise ValueError("Plane must be axial, coronal, or sagittal.")
    _, count, extractor = planes[plane]
    if not 0 <= index < count:
        raise IndexError(f"Slice index must be between 0 and {count - 1}.")
    slice_data = extractor(index)
    figure = go.Figure(go.Heatmap(z=slice_data, colorscale="Gray", showscale=False))
    figure.update_layout(title=f"{plane.title()} slice {index + 1}/{count}", margin=dict(l=5, r=5, t=40, b=5))
    figure.update_yaxes(autorange="reversed", scaleanchor="x")
    return figure


def make_volume_figure(volume: MRIVolume, max_dimension: int = 48) -> go.Figure:
    """Create an interactive Plotly volume rendering, downsampling only the display copy."""
    if max_dimension < 8:
        raise ValueError("max_dimension must be at least 8.")
    data = volume.data
    if float(np.max(data)) <= float(np.min(data)):
        raise ValueError("Cannot render a constant-intensity volume.")
    strides = tuple(max(1, math.ceil(size / max_dimension)) for size in data.shape)
    display = data[::strides[0], ::strides[1], ::strides[2]]
    z_size, y_size, x_size = display.shape
    z = np.arange(z_size, dtype=np.float32) * volume.spacing_mm[0] * strides[0]
    y = np.arange(y_size, dtype=np.float32) * volume.spacing_mm[1] * strides[1]
    x = np.arange(x_size, dtype=np.float32) * volume.spacing_mm[2] * strides[2]
    zz, yy, xx = np.meshgrid(z, y, x, indexing="ij")
    low, high = np.percentile(display, [15, 99])
    if high <= low:
        high = float(np.max(display))
    figure = go.Figure(data=go.Volume(
        x=xx.ravel(), y=yy.ravel(), z=zz.ravel(), value=display.ravel(),
        isomin=float(low), isomax=float(high), opacity=0.08, surface_count=12,
        colorscale="Gray", caps=dict(x_show=False, y_show=False, z_show=False),
    ))
    figure.update_layout(
        title="3D MRI intensity volume (not a tumor segmentation)",
        scene=dict(xaxis_title="X (mm)", yaxis_title="Y (mm)", zaxis_title="Z (mm)", aspectmode="data"),
        margin=dict(l=0, r=0, t=45, b=0),
    )
    return figure
