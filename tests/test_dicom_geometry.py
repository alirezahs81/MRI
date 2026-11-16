"""Synthetic DICOM series tests for ordering, rescaling, and spatial geometry."""

import numpy as np
import pydicom
import pytest
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from src.multimodal import check_geometry_compatibility
from src.volume_io import load_dicom_series


def _write_slice(path, *, instance, z, pixels, series_uid, orientation=None, spacing=(1.0, 1.5)):
    meta = FileMetaDataset()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.MediaStorageSOPClassUID = pydicom.uid.MRImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    ds = FileDataset(str(path), {}, file_meta=meta, preamble=b"\x00" * 128)
    ds.SOPClassUID = meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.SeriesInstanceUID = series_uid
    ds.Modality = "MR"
    ds.Rows, ds.Columns = pixels.shape
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.InstanceNumber = instance
    ds.PixelSpacing = list(spacing)
    ds.SliceThickness = 2.0
    ds.RescaleSlope = 2.0
    ds.RescaleIntercept = -10.0
    if orientation is not None:
        ds.ImageOrientationPatient = orientation
        ds.ImagePositionPatient = [0.0, 0.0, float(z)]
    ds.PixelData = np.asarray(pixels, dtype="<i2").tobytes()
    ds.save_as(path, enforce_file_format=True)


def test_dicom_series_is_sorted_and_has_patient_space_affine(tmp_path):
    uid = generate_uid()
    _write_slice(tmp_path / "slice2.dcm", instance=2, z=2, pixels=np.full((3, 4), 2), series_uid=uid,
                 orientation=[1, 0, 0, 0, 1, 0])
    _write_slice(tmp_path / "slice0.dcm", instance=0, z=0, pixels=np.zeros((3, 4)), series_uid=uid,
                 orientation=[1, 0, 0, 0, 1, 0])
    _write_slice(tmp_path / "slice1.dcm", instance=1, z=1, pixels=np.ones((3, 4)), series_uid=uid,
                 orientation=[1, 0, 0, 0, 1, 0])

    volume = load_dicom_series(tmp_path)
    assert volume.data.shape == (3, 3, 4)
    np.testing.assert_allclose(volume.data[:, 0, 0], [-10.0, -8.0, -6.0])
    assert volume.spacing_mm == pytest.approx((1.0, 1.0, 1.5))
    np.testing.assert_allclose(volume.affine[:3, 0], [1.5, 0, 0])
    np.testing.assert_allclose(volume.affine[:3, 1], [0, 1.0, 0])
    np.testing.assert_allclose(volume.affine[:3, 2], [0, 0, 1.0])
    np.testing.assert_allclose(volume.affine[:3, 3], [0, 0, 0])
    assert volume.metadata["spatial_geometry_verified"]


def test_dicom_series_rejects_inconsistent_orientation(tmp_path):
    uid = generate_uid()
    _write_slice(tmp_path / "a.dcm", instance=1, z=0, pixels=np.zeros((3, 4)), series_uid=uid,
                 orientation=[1, 0, 0, 0, 1, 0])
    _write_slice(tmp_path / "b.dcm", instance=2, z=1, pixels=np.zeros((3, 4)), series_uid=uid,
                 orientation=[0, 1, 0, -1, 0, 0])
    with pytest.raises(ValueError, match="inconsistent ImageOrientationPatient"):
        load_dicom_series(tmp_path)


def test_dicom_series_rejects_mixed_series_uids(tmp_path):
    _write_slice(tmp_path / "a.dcm", instance=1, z=0, pixels=np.zeros((3, 4)), series_uid=generate_uid(),
                 orientation=[1, 0, 0, 0, 1, 0])
    _write_slice(tmp_path / "b.dcm", instance=2, z=1, pixels=np.zeros((3, 4)), series_uid=generate_uid(),
                 orientation=[1, 0, 0, 0, 1, 0])
    with pytest.raises(ValueError, match="multiple DICOM series"):
        load_dicom_series(tmp_path)


def test_dicom_without_spatial_tags_is_not_claimed_aligned(tmp_path):
    uid = generate_uid()
    _write_slice(tmp_path / "a.dcm", instance=1, z=0, pixels=np.zeros((3, 4)), series_uid=uid)
    _write_slice(tmp_path / "b.dcm", instance=2, z=1, pixels=np.ones((3, 4)), series_uid=uid)
    volume = load_dicom_series(tmp_path)
    assert volume.affine is None
    assert not volume.metadata["spatial_geometry_verified"]
    other = load_dicom_series(tmp_path)
    compatible, reason = check_geometry_compatibility(volume, other)
    assert not compatible
    assert "affine" in reason.lower()


def test_dicom_series_rejects_non_uniform_slice_positions(tmp_path):
    uid = generate_uid()
    for index, z in enumerate((0.0, 1.0, 3.0)):
        _write_slice(tmp_path / f"{index}.dcm", instance=index, z=z, pixels=np.zeros((3, 4)),
                     series_uid=uid, orientation=[1, 0, 0, 0, 1, 0])
    with pytest.raises(ValueError, match="non-uniform"):
        load_dicom_series(tmp_path)



def test_dicom_series_rejects_missing_series_uid(tmp_path):
    _write_slice(
        tmp_path / "a.dcm", instance=1, z=0, pixels=np.zeros((3, 4)),
        series_uid="", orientation=[1, 0, 0, 0, 1, 0],
    )
    _write_slice(
        tmp_path / "b.dcm", instance=2, z=1, pixels=np.zeros((3, 4)),
        series_uid="", orientation=[1, 0, 0, 0, 1, 0],
    )
    with pytest.raises(ValueError, match="same non-empty SeriesInstanceUID"):
        load_dicom_series(tmp_path)


def test_dicom_series_affine_is_converted_from_lps_to_ras(tmp_path):
    uid = generate_uid()
    _write_slice(
        tmp_path / "a.dcm", instance=1, z=10, pixels=np.zeros((3, 4)),
        series_uid=uid, orientation=[1, 0, 0, 0, 1, 0],
    )
    _write_slice(
        tmp_path / "b.dcm", instance=2, z=11, pixels=np.zeros((3, 4)),
        series_uid=uid, orientation=[1, 0, 0, 0, 1, 0],
    )
    volume = load_dicom_series(tmp_path)
    np.testing.assert_allclose(volume.affine[:3, 0], [-1.5, 0, 0])
    np.testing.assert_allclose(volume.affine[:3, 1], [0, -1.0, 0])
    np.testing.assert_allclose(volume.affine[:3, 2], [0, 0, 1.0])
    np.testing.assert_allclose(volume.affine[:3, 3], [0, 0, 10.0])


def test_dicom_series_rejects_mixed_temporal_positions(tmp_path):
    uid = generate_uid()
    _write_slice(
        tmp_path / "a.dcm", instance=1, z=0, pixels=np.zeros((3, 4)),
        series_uid=uid, orientation=[1, 0, 0, 0, 1, 0],
    )
    _write_slice(
        tmp_path / "b.dcm", instance=2, z=1, pixels=np.zeros((3, 4)),
        series_uid=uid, orientation=[1, 0, 0, 0, 1, 0],
    )
    # Add a distinct temporal position to one member: this must not be stacked.
    ds = pydicom.dcmread(str(tmp_path / "b.dcm"))
    ds.TemporalPositionIdentifier = 2
    ds.save_as(tmp_path / "b.dcm", enforce_file_format=True)
    ds = pydicom.dcmread(str(tmp_path / "a.dcm"))
    ds.TemporalPositionIdentifier = 1
    ds.save_as(tmp_path / "a.dcm", enforce_file_format=True)
    with pytest.raises(ValueError, match="TemporalPositionIdentifier"):
        load_dicom_series(tmp_path)



def test_dicom_series_rejects_missing_pixel_spacing(tmp_path):
    uid = generate_uid()
    _write_slice(
        tmp_path / "a.dcm", instance=1, z=0, pixels=np.zeros((3, 4)),
        series_uid=uid, orientation=[1, 0, 0, 0, 1, 0],
    )
    _write_slice(
        tmp_path / "b.dcm", instance=2, z=1, pixels=np.zeros((3, 4)),
        series_uid=uid, orientation=[1, 0, 0, 0, 1, 0],
    )
    ds = pydicom.dcmread(str(tmp_path / "b.dcm"))
    del ds.PixelSpacing
    ds.save_as(tmp_path / "b.dcm", enforce_file_format=True)
    with pytest.raises(ValueError, match="PixelSpacing"):
        load_dicom_series(tmp_path)
