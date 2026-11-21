"""Unit tests for privacy-preserving local MRI validation summaries."""
import numpy as np

from scripts.validate_mri import render_markdown, validate_volume
from src.volume_io import MRIVolume


def _volume(affine=True, geometry=True):
    transform = np.diag([-1.0, -1.0, 2.0, 1.0]) if affine else None
    return MRIVolume(
        data=np.arange(24, dtype=np.float32).reshape(2, 3, 4),
        spacing_mm=(2.0, 1.0, 1.0),
        source=r"C:\private\patient\study",
        affine=transform,
        metadata={
            "format": "DICOM",
            "spatial_geometry_verified": geometry,
            "series_instance_uid": "SECRET-UID",
            "series_description": "SECRET-SERIES",
            "patient_id_present": True,
        },
    )


def test_report_has_expected_nonidentifying_summary():
    report = validate_volume(_volume())
    assert report["volume_shape_zyx"] == [2, 3, 4]
    assert report["slice_count"] == 2
    assert report["voxel_spacing_mm_zyx"] == [2.0, 1.0, 1.0]
    assert report["spatial_affine_valid"] is True
    assert report["spatial_geometry_verified"] is True
    assert report["clinical_validation_performed"] is False


def test_report_does_not_leak_paths_or_dicom_identifiers():
    report = validate_volume(_volume())
    text = render_markdown(report)
    serialized = str(report) + text
    for secret in ("C:\\private", "SECRET-UID", "SECRET-SERIES", "patient"):
        assert secret.lower() not in serialized.lower()


def test_missing_affine_generates_clear_warning():
    report = validate_volume(_volume(affine=False, geometry=False))
    assert report["spatial_affine_valid"] is False
    assert report["ras_axis_orientation"] is None
    assert any("affine" in warning.lower() for warning in report["warnings"])
