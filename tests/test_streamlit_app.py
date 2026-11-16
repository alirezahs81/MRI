"""Headless end-to-end tests for the Streamlit MRI upload interface."""

from io import BytesIO
from pathlib import Path
import zipfile

import nibabel as nib
import numpy as np
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid
from streamlit.testing.v1 import AppTest


def _make_nifti_bytes(tmp_path, name="sample_flair.nii.gz"):
    """Create a small valid NIfTI file and return its serialized bytes."""
    data = np.arange(12 * 10 * 8, dtype=np.float32).reshape((12, 10, 8))
    affine = np.diag([1.0, 1.2, 2.0, 1.0])
    path = tmp_path / name
    nib.save(nib.Nifti1Image(data, affine), path)
    return path.read_bytes()


def _make_dicom_zip_bytes(tmp_path):
    """Build a tiny, deterministic conventional DICOM series in a ZIP archive."""
    series_uid = generate_uid()
    dicom_dir = tmp_path / "dicom_series"
    dicom_dir.mkdir()

    for index in (2, 0, 1):
        path = dicom_dir / f"slice_{index}.dcm"
        file_meta = FileMetaDataset()
        file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        file_meta.MediaStorageSOPClassUID = pydicom.uid.MRImageStorage
        file_meta.MediaStorageSOPInstanceUID = generate_uid()

        dataset = FileDataset(
            str(path), {}, file_meta=file_meta, preamble=bytes(128)
        )
        dataset.SOPClassUID = file_meta.MediaStorageSOPClassUID
        dataset.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        dataset.SeriesInstanceUID = series_uid
        dataset.Modality = "MR"
        dataset.Rows = 8
        dataset.Columns = 8
        dataset.SamplesPerPixel = 1
        dataset.PhotometricInterpretation = "MONOCHROME2"
        dataset.BitsAllocated = 16
        dataset.BitsStored = 16
        dataset.HighBit = 15
        dataset.PixelRepresentation = 0
        dataset.InstanceNumber = index + 1
        dataset.PixelSpacing = [1.0, 1.0]
        dataset.SliceThickness = 1.0
        dataset.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        dataset.ImagePositionPatient = [0, 0, float(index)]
        pixels = np.full((8, 8), index + 1, dtype="<u2")
        dataset.PixelData = pixels.tobytes()
        dataset.save_as(path, enforce_file_format=True)

    archive_buffer = BytesIO()
    with zipfile.ZipFile(archive_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(dicom_dir.glob("*.dcm")):
            archive.write(path, arcname=f"series/{path.name}")
    return archive_buffer.getvalue()


def test_streamlit_app_accepts_and_processes_nifti_upload(tmp_path):
    """Exercise the actual app entrypoint with a synthetic uploaded MRI volume."""
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(app_path).run()
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


def test_streamlit_app_accepts_and_processes_dicom_series_zip_upload(tmp_path):
    """Exercise ZIP extraction, DICOM loading, and viewer rendering end to end."""
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(app_path).run()
    assert not app.exception

    app.file_uploader[0].upload(
        "sample_dicom.zip",
        _make_dicom_zip_bytes(tmp_path),
        "application/zip",
    )
    app.run()

    assert not app.exception
    assert any(
        "Loaded 1 MRI sequence(s)." in element.value
        for element in app.success
    )
    assert any("Other — sample_dicom.zip" in element.value for element in app.subheader)
