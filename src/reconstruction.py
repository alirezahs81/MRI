"""Orthogonal slice and physical-space 3D visualization for MRI volumes."""

from __future__ import annotations

import math

import numpy as np
import plotly.graph_objects as go

from src.volume_io import MRIVolume


def make_slice_figure(volume: MRIVolume, plane: str, index: int) -> go.Figure:
    """Create an axial, coronal, or sagittal slice view."""
    planes = {
        "axis-0": (volume.data.shape[0], lambda i: volume.data[i, :, :]),
        "axis-1": (volume.data.shape[1], lambda i: volume.data[:, i, :]),
        "axis-2": (volume.data.shape[2], lambda i: volume.data[:, :, i]),
    }
    if plane not in planes:
        raise ValueError("Plane must be axial, coronal, or sagittal.")
    count, extractor = planes[plane]
    if not 0 <= index < count:
        raise IndexError(f"Slice index must be between 0 and {count - 1}.")
    figure = go.Figure(go.Heatmap(z=extractor(index), colorscale="Gray", showscale=False))
    figure.update_layout(
        title=f"{plane.replace('-', ' ').title()} slice {index + 1}/{count}",
        margin=dict(l=5, r=5, t=40, b=5),
    )
    figure.update_yaxes(autorange="reversed", scaleanchor="x")
    return figure


def _display_grid(
    volume: MRIVolume, max_dimension: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return a downsampled volume and coordinates in its declared world space."""
    if max_dimension < 8:
        raise ValueError("max_dimension must be at least 8.")
    data = volume.data
    strides = tuple(max(1, math.ceil(size / max_dimension)) for size in data.shape)
    display = data[::strides[0], ::strides[1], ::strides[2]]
    z = np.arange(display.shape[0], dtype=np.float64) * strides[0]
    y = np.arange(display.shape[1], dtype=np.float64) * strides[1]
    x = np.arange(display.shape[2], dtype=np.float64) * strides[2]
    zz, yy, xx = np.meshgrid(z, y, x, indexing="ij")

    if volume.affine is not None:
        voxel_xyz = np.stack(
            [xx.ravel(), yy.ravel(), zz.ravel(), np.ones(xx.size)], axis=0
        )
        world_xyz = np.asarray(volume.affine, dtype=float) @ voxel_xyz
        world_xyz = world_xyz[:3].reshape(3, *display.shape)
        return display, world_xyz[0], world_xyz[1], world_xyz[2]

    # If orientation is unavailable, retain only relative axis distances and
    # avoid claiming that these are patient/world coordinates.
    xx *= volume.spacing_mm[2]
    yy *= volume.spacing_mm[1]
    zz *= volume.spacing_mm[0]
    return display, xx, yy, zz


def make_volume_figure(volume: MRIVolume, max_dimension: int = 48) -> go.Figure:
    """Create a 3D intensity volume rendering; downsample only the display copy."""
    display, xx, yy, zz = _display_grid(volume, max_dimension)
    if float(np.max(display)) <= float(np.min(display)):
        raise ValueError("Cannot render a constant-intensity volume.")
    low, high = np.percentile(display, [15, 99])
    if high <= low:
        high = float(np.max(display))
    figure = go.Figure(data=go.Volume(
        x=xx.ravel(), y=yy.ravel(), z=zz.ravel(), value=display.ravel(),
        isomin=float(low), isomax=float(high), opacity=0.08, surface_count=14,
        colorscale="Gray", caps=dict(x_show=False, y_show=False, z_show=False),
    ))
    figure.update_layout(
        title="3D MRI intensity volume (not a tumor segmentation)",
        scene=dict(
            xaxis_title="RAS X (mm)" if volume.affine is not None else "Relative X (mm; orientation unknown)",
            yaxis_title="RAS Y (mm)" if volume.affine is not None else "Relative Y (mm; orientation unknown)",
            zaxis_title="RAS Z (mm)" if volume.affine is not None else "Relative Z (mm; orientation unknown)",
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, t=45, b=0),
    )
    return figure


def make_isosurface_figure(volume: MRIVolume, max_dimension: int = 64) -> go.Figure:
    """Create exploratory intensity isosurfaces; this is not anatomical or tumor segmentation."""
    display, xx, yy, zz = _display_grid(volume, max_dimension)
    low_value, high_value = float(np.min(display)), float(np.max(display))
    if high_value <= low_value:
        raise ValueError("Cannot create an isosurface from a constant-intensity volume.")
    lower, upper = np.percentile(display, [55, 90])
    if upper <= lower:
        lower, upper = low_value, high_value
    figure = go.Figure(data=go.Isosurface(
        x=xx.ravel(), y=yy.ravel(), z=zz.ravel(), value=display.ravel(),
        isomin=float(lower), isomax=float(upper), surface_count=3,
        colorscale="Gray", caps=dict(x_show=False, y_show=False, z_show=False),
        opacity=0.35, showscale=False,
    ))
    figure.update_layout(
        title="Exploratory MRI intensity isosurface (not anatomical segmentation)",
        scene=dict(
            xaxis_title="RAS X (mm)" if volume.affine is not None else "Relative X (mm; orientation unknown)",
            yaxis_title="RAS Y (mm)" if volume.affine is not None else "Relative Y (mm; orientation unknown)",
            zaxis_title="RAS Z (mm)" if volume.affine is not None else "Relative Z (mm; orientation unknown)",
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, t=45, b=0),
    )
    return figure
