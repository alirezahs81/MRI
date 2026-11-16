import numpy as np
import nibabel as nib
import pytest

from src.volume_io import load_dicom_series, load_nifti, load_volume


def test_load_nifti_returns_zyx_and_physical_spacing(tmp_path):
    source = np.arange(4 * 5 * 6, dtype=np.float32).reshape(4, 5, 6)
    affine = np.diag([1.0, 1.5, 2.0, 1.0])
    path = tmp_path / "sample.nii.gz"
    nib.save(nib.Nifti1Image(source, affine), path)

    result = load_nifti(path)
    assert result.data.shape == (6, 5, 4)
    assert result.spacing_mm == pytest.approx((2.0, 1.5, 1.0))
    assert result.metadata["format"] == "NIfTI"


def test_load_volume_dispatches_nifti(tmp_path):
    path = tmp_path / "tiny.nii"
    nib.save(nib.Nifti1Image(np.ones((3, 4, 5), dtype=np.float32), np.eye(4)), path)
    assert load_volume(path).data.shape == (5, 4, 3)


def test_empty_dicom_directory_fails_clearly(tmp_path):
    with pytest.raises(ValueError, match="No readable"):
        load_dicom_series(tmp_path)


def test_unsupported_file_fails_clearly(tmp_path):
    path = tmp_path / "scan.jpg"
    path.write_bytes(b"not an MRI")
    with pytest.raises(ValueError, match="Unsupported input"):
        load_volume(path)
