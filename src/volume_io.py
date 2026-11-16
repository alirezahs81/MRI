"""Load spatially-aware MRI volumes from NIfTI files and DICOM series."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import nibabel as nib
import numpy as np
import pydicom


@dataclass
class MRIVolume:
    """MRI volume stored in (z, y, x) array order with spacing in millimetres."""

    data: np.ndarray
    spacing_mm: tuple[float, float, float]
    source: str
    modality: str = "MRI"
    affine: np.ndarray | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.data = np.asarray(self.data, dtype=np.float32)
        if self.data.ndim != 3 or any(size < 1 for size in self.data.shape):
            raise ValueError("MRI volume must be a non-empty 3D array in (z, y, x) order.")
        if not np.isfinite(self.data).all():
            raise ValueError("MRI volume contains NaN or infinite voxel values.")
        if len(self.spacing_mm) != 3 or any(not np.isfinite(v) or v <= 0 for v in self.spacing_mm):
            raise ValueError("Voxel spacing must contain three positive finite values in millimetres.")


def load_nifti(path: str | Path) -> MRIVolume:
    """Load a 3D NIfTI image, reorient it to closest canonical orientation, and return (z,y,x)."""
    image_path = Path(path)
    if not image_path.is_file():
        raise FileNotFoundError(f"NIfTI file not found: {image_path}")
    image = nib.as_closest_canonical(nib.load(str(image_path)))
    data_xyz = np.asarray(image.get_fdata(dtype=np.float32))
    if data_xyz.ndim != 3:
        raise ValueError(f"Expected a 3D NIfTI volume, received {data_xyz.ndim} dimensions.")
    zooms = image.header.get_zooms()[:3]
    data_zyx = np.transpose(data_xyz, (2, 1, 0))
    return MRIVolume(
        data=data_zyx,
        spacing_mm=(float(zooms[2]), float(zooms[1]), float(zooms[0])),
        source=str(image_path),
        affine=np.asarray(image.affine, dtype=float),
        metadata={"format": "NIfTI", "canonical_orientation": True},
    )


def load_dicom_series(directory: str | Path) -> MRIVolume:
    """Load one conventional single-frame DICOM series; reject mixed series instead of merging them."""
    root = Path(directory)
    if not root.is_dir():
        raise NotADirectoryError(f"DICOM input must be a directory: {root}")

    datasets = []
    for file_path in sorted(p for p in root.rglob("*") if p.is_file()):
        try:
            ds = pydicom.dcmread(str(file_path), force=False)
            if hasattr(ds, "PixelData") and hasattr(ds, "Rows") and hasattr(ds, "Columns"):
                if int(getattr(ds, "NumberOfFrames", 1)) == 1:
                    datasets.append((file_path, ds))
        except Exception:
            continue

    if not datasets:
        raise ValueError(f"No readable single-frame DICOM images with pixel data were found in {root}.")

    series_uids = {str(getattr(ds, "SeriesInstanceUID", "")) for _, ds in datasets}
    series_uids.discard("")
    if len(series_uids) > 1:
        raise ValueError(
            "This folder contains multiple DICOM series. Upload each sequence/series separately "
            "so slices from different acquisitions are never mixed."
        )
    if series_uids:
        selected_uid = next(iter(series_uids))
        datasets = [(path, ds) for path, ds in datasets
                    if str(getattr(ds, "SeriesInstanceUID", "")) == selected_uid]

    first = datasets[0][1]
    orientation = getattr(first, "ImageOrientationPatient", None)
    normal = None
    if orientation is not None and len(orientation) == 6:
        row = np.asarray(orientation[:3], dtype=float)
        column = np.asarray(orientation[3:], dtype=float)
        normal = np.cross(row, column)
        norm = np.linalg.norm(normal)
        normal = normal / norm if norm else None

    def sort_key(item: tuple[Path, Any]) -> tuple[int, float]:
        ds = item[1]
        position = getattr(ds, "ImagePositionPatient", None)
        if normal is not None and position is not None and len(position) == 3:
            return (0, float(np.dot(np.asarray(position, dtype=float), normal)))
        return (1, float(getattr(ds, "InstanceNumber", 0)))

    datasets.sort(key=sort_key)
    arrays = []
    for file_path, ds in datasets:
        pixels = np.asarray(ds.pixel_array, dtype=np.float32)
        if pixels.ndim != 2:
            continue
        pixels = pixels * float(getattr(ds, "RescaleSlope", 1.0)) + float(getattr(ds, "RescaleIntercept", 0.0))
        arrays.append((file_path, ds, pixels))

    if not arrays:
        raise ValueError("DICOM series contains no supported 2D pixel arrays.")
    shapes = {entry[2].shape for entry in arrays}
    if len(shapes) != 1:
        raise ValueError(f"DICOM slices have inconsistent dimensions: {sorted(shapes)}")

    volume = np.stack([entry[2] for entry in arrays], axis=0)
    ds0 = arrays[0][1]
    pixel_spacing = getattr(ds0, "PixelSpacing", (1.0, 1.0))
    row_spacing, column_spacing = float(pixel_spacing[0]), float(pixel_spacing[1])

    z_spacing = float(getattr(ds0, "SpacingBetweenSlices", getattr(ds0, "SliceThickness", 1.0)))
    positions = [getattr(entry[1], "ImagePositionPatient", None) for entry in arrays]
    if normal is not None and all(position is not None for position in positions) and len(positions) > 1:
        projections = [float(np.dot(np.asarray(position, dtype=float), normal)) for position in positions]
        differences = np.abs(np.diff(projections))
        nonzero = differences[differences > 1e-6]
        if nonzero.size:
            z_spacing = float(np.median(nonzero))

    return MRIVolume(
        data=volume,
        spacing_mm=(z_spacing, row_spacing, column_spacing),
        source=str(root),
        modality=str(getattr(ds0, "Modality", "MRI")),
        metadata={
            "format": "DICOM",
            "slices_loaded": int(volume.shape[0]),
            "series_instance_uid": str(getattr(ds0, "SeriesInstanceUID", "")),
            "series_description": str(getattr(ds0, "SeriesDescription", "")),
            "patient_id_present": bool(getattr(ds0, "PatientID", "")),
            "image_orientation_patient": list(orientation) if orientation is not None else None,
        },
    )


def load_volume(path: str | Path) -> MRIVolume:
    """Dispatch to NIfTI loading for files or DICOM loading for directories."""
    source = Path(path)
    if source.is_dir():
        return load_dicom_series(source)
    lower_name = source.name.lower()
    if lower_name.endswith(".nii") or lower_name.endswith(".nii.gz"):
        return load_nifti(source)
    raise ValueError("Unsupported input. Provide a DICOM directory, .nii file, or .nii.gz file.")
