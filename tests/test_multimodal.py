import numpy as np

from src.multimodal import check_geometry_compatibility
from src.volume_io import MRIVolume


def make_volume(*, shape=(5, 6, 7), affine=None, spacing=(1.0, 1.0, 1.0)):
    return MRIVolume(
        data=np.zeros(shape, dtype=np.float32),
        spacing_mm=spacing,
        source="geometry-test",
        affine=np.eye(4) if affine is None else affine,
    )


def test_matching_shape_affine_and_spacing_are_compatible():
    compatible, reason = check_geometry_compatibility(make_volume(), make_volume())
    assert compatible
    assert "Matching" in reason


def test_shape_mismatch_is_not_compatible():
    compatible, reason = check_geometry_compatibility(
        make_volume(), make_volume(shape=(5, 6, 8))
    )
    assert not compatible
    assert "Shape mismatch" in reason


def test_affine_mismatch_is_not_compatible():
    shifted = np.eye(4)
    shifted[0, 3] = 2.0
    compatible, reason = check_geometry_compatibility(
        make_volume(), make_volume(affine=shifted)
    )
    assert not compatible
    assert "affine" in reason.lower()


def test_spacing_mismatch_is_not_compatible():
    compatible, reason = check_geometry_compatibility(
        make_volume(), make_volume(spacing=(2.0, 1.0, 1.0))
    )
    assert not compatible
    assert "spacing" in reason.lower()


def test_missing_affine_is_not_assumed_compatible():
    compatible, reason = check_geometry_compatibility(
        make_volume(), make_volume(affine=None)
    )
    # make_volume defaults to identity; explicitly test unavailable metadata.
    candidate = MRIVolume(
        data=np.zeros((5, 6, 7), dtype=np.float32),
        spacing_mm=(1.0, 1.0, 1.0),
        source="dicom-without-affine",
        affine=None,
    )
    compatible, reason = check_geometry_compatibility(make_volume(), candidate)
    assert not compatible
    assert "affine" in reason.lower()
