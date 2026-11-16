"""Headless end-to-end tests for the Streamlit MRI upload interface."""

import nibabel as nib
import numpy as np
from streamlit.testing.v1 import AppTest


def _make_nifti_bytes(tmp_path, name="sample_flair.nii.gz"):
    """Create a small valid NIfTI file and return its serialized bytes."""
    data = np.arange(12 * 10 * 8, dtype=np.float32).reshape((12, 10, 8))
    affine = np.diag([1.0, 1.2, 2.0, 1.0])
    path = tmp_path / name
    nib.save(nib.Nifti1Image(data, affine), path)
    return path.read_bytes()


def test_streamlit_app_accepts_and_processes_nifti_upload(tmp_path):
    """Exercise the actual app entrypoint with a synthetic uploaded MRI volume."""
    app = AppTest.from_file("app.py").run()
    assert not app.exception
    assert len(app.file_uploader) == 1

    app.file_uploader[0].upload(
        "sample_flair.nii.gz",
        _make_nifti_bytes(tmp_path),
        "application/gzip",
    )
    app.run()

    assert not app.exception
    assert any(
        "Loaded 1 MRI sequence(s)." in element.value
        for element in app.success
    )
    assert any("FLAIR" in element.value for element in app.subheader)
