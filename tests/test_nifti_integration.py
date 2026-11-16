"""Integration tests using temporary NIfTI files written to disk.

These tests exercise the real NIfTI serialization/loading path without
committing medical images or relying on external datasets.
"""

import nibabel as nib
import numpy as np
import pytest

from src.multimodal import check_geometry_compatibility
from src.reconstruction import (
    make_isosurface_figure,
    make_slice_figure,
    make_volume_figure,
)
from src.volume_io import load_volume


def _write_nifti(path, data_xyz, affine):
    nib.save(nib.Nifti1Image(data_xyz.astype(np.float32), affine), path)
    return path


def test_real_nifti_files_load_align_and_render_end_to_end(tmp_path):
    """Load two on-disk NIfTI sequences and exercise the downstream viewer path."""
    rng = np.random.default_rng(2026)
    shape_xyz = (24, 20, 16)
    flair_xyz = rng.normal(loc=80.0, scale=20.0, size=shape_xyz).astype(np.float32)
    t1_xyz = (flair_xyz * 1.7 + rng.normal(0.0, 5.0, size=shape_xyz)).astype(
        np.float32
    )
    affine = np.diag([1.0, 1.2, 2.0, 1.0])

    flair_path = _write_nifti(tmp_path / "sample_flair.nii.gz", flair_xyz, affine)
    t1_path = _write_nifti(tmp_path / "sample_t1.nii.gz", t1_xyz, affine)

    flair = load_volume(flair_path)
    t1 = load_volume(t1_path)

    expected_shape_zyx = (16, 20, 24)
    assert flair.data.shape == expected_shape_zyx
    assert t1.data.shape == expected_shape_zyx
    assert flair.spacing_mm == pytest.approx((2.0, 1.2, 1.0))
    assert t1.spacing_mm == pytest.approx((2.0, 1.2, 1.0))
    np.testing.assert_allclose(flair.data, np.transpose(flair_xyz, (2, 1, 0)))
    np.testing.assert_allclose(t1.data, np.transpose(t1_xyz, (2, 1, 0)))

    compatible, reason = check_geometry_compatibility(flair, t1)
    assert compatible, reason

    for plane, axis in (("axial", 0), ("coronal", 1), ("sagittal", 2)):
        figure = make_slice_figure(flair, plane, flair.data.shape[axis] // 2)
        assert len(figure.data) == 1
        assert figure.data[0].type == "heatmap"

    volume_figure = make_volume_figure(flair, max_dimension=16)
    assert len(volume_figure.data) == 1
    assert volume_figure.data[0].type == "volume"

    isosurface_figure = make_isosurface_figure(flair, max_dimension=16)
    assert len(isosurface_figure.data) == 1
    assert isosurface_figure.data[0].type == "isosurface"
