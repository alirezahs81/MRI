"""Load spatially-aware MRI volumes from NIfTI files and DICOM series."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import prod
from pathlib import Path
from typing import Any

import nibabel as nib
import numpy as np
import pydicom


MAX_VOLUME_VOXELS = 32_000_000
MAX_DICOM_SLICES = 10_000


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
        if len(self.spacing_mm) != 3 or any(
            not np.isfinite(v) or v <= 0 for v in self.spacing_mm
        ):
            raise ValueError("Voxel spacing must contain three positive finite values in millimetres.")
        if self.affine is not None:
            affine = np.asarray(self.affine, dtype=float)
            if affine.shape != (4, 4) or not np.isfinite(affine).all():
                raise ValueError("Spatial affine must be a finite 4x4 matrix.")
            if not np.allclose(affine[3], [0.0, 0.0, 0.0, 1.0], atol=1e-8):
                raise ValueError("Spatial affine must have a valid homogeneous last row.")
            if abs(float(np.linalg.det(affine[:3, :3]))) <= 1e-8:
                raise ValueError("Spatial affine must be non-singular.")
            self.affine = affine


def load_nifti(path: str | Path) -> MRIVolume:
    """Load a 3D NIfTI image, reorient it to closest canonical orientation, and return (z,y,x)."""
    image_path = Path(path)
    if not image_path.is_file():
        raise FileNotFoundError(f"NIfTI file not found: {image_path}")
    image = nib.load(str(image_path))
    if len(image.shape) != 3:
        raise ValueError(f"Expected a 3D NIfTI volume, received {len(image.shape)} dimensions.")
    voxel_count = prod(int(size) for size in image.shape)
    if voxel_count > MAX_VOLUME_VOXELS:
        raise ValueError(
            f"NIfTI volume contains {voxel_count:,} voxels; the safety limit is "
            f"{MAX_VOLUME_VOXELS:,}."
        )
    image = nib.as_closest_canonical(image)
    data_xyz = np.asarray(image.get_fdata(dtype=np.float32))
    zooms = image.header.get_zooms()[:3]
    data_zyx = np.transpose(data_xyz, (2, 1, 0))
    return MRIVolume(
        data=data_zyx,
        spacing_mm=(float(zooms[2]), float(zooms[1]), float(zooms[0])),
        source=str(image_path),
        affine=np.asarray(image.affine, dtype=float),
        metadata={"format": "NIfTI", "canonical_orientation": True},
    )


def _dicom_vector(value: Any, name: str, length: int) -> np.ndarray:
    """Parse a finite DICOM direction/position vector with the expected length."""
    vector = np.asarray(value, dtype=float)
    if vector.shape != (length,) or not np.isfinite(vector).all():
        raise ValueError(f"Invalid DICOM {name}; expected {length} finite values.")
    return vector


def load_dicom_series(directory: str | Path) -> MRIVolume:
    """Load one geometrically consistent conventional single-frame DICOM series."""
    root = Path(directory)
    if not root.is_dir():
        raise NotADirectoryError(f"DICOM input must be a directory: {root}")

    datasets = []
    for file_path in sorted(p for p in root.rglob("*") if p.is_file()):
        try:
            ds = pydicom.dcmread(str(file_path), force=False)
        except Exception as exc:
            # Ignore obvious non-DICOM sidecar files, but never silently skip a
            # file explicitly named as DICOM: that could create a partial series.
            if file_path.suffix.lower() in {".dcm", ".dicom"}:
                raise ValueError(f"Could not read DICOM file: {file_path.name}.") from exc
            continue

        if hasattr(ds, "PixelData") and hasattr(ds, "Rows") and hasattr(ds, "Columns"):
            frame_count = int(getattr(ds, "NumberOfFrames", 1))
            if frame_count != 1:
                raise ValueError(
                    "Multi-frame DICOM is not supported. Convert to a conventional "
                    "single-frame series before loading."
                )
            datasets.append((file_path, ds))

    if not datasets:
        raise ValueError(f"No readable single-frame DICOM images with pixel data were found in {root}.")
    if len(datasets) > MAX_DICOM_SLICES:
        raise ValueError(
            f"DICOM series contains too many slices ({len(datasets):,}); "
            f"the safety limit is {MAX_DICOM_SLICES:,}."
        )
    modalities = {str(getattr(ds, "Modality", "")).strip().upper() for _, ds in datasets}
    if modalities != {"MR"}:
        raise ValueError("Only DICOM MR modality images are supported.")

    series_uids = {str(getattr(ds, "SeriesInstanceUID", "")).strip() for _, ds in datasets}
    if len(series_uids) != 1 or "" in series_uids:
        raise ValueError(
            "This folder contains multiple DICOM series or missing/inconsistent SeriesInstanceUID metadata. "
            "Every image must have the same non-empty SeriesInstanceUID; upload one complete series at a time."
        )

    # Do not combine distinct acquisitions, echoes, or temporal positions into
    # one 3D volume even when a sender reused a SeriesInstanceUID incorrectly.
    consistency_tags = (
        ("Modality", "Modality"),
        ("FrameOfReferenceUID", "FrameOfReferenceUID"),
        ("AcquisitionNumber", "AcquisitionNumber"),
        ("TemporalPositionIdentifier", "TemporalPositionIdentifier"),
        ("EchoNumbers", "EchoNumbers"),
    )
    for attribute, label in consistency_tags:
        values = [str(getattr(ds, attribute, "")).strip() for _, ds in datasets]
        present = [value for value in values if value]
        if present and (len(present) != len(values) or len(set(present)) != 1):
            raise ValueError(
                f"DICOM slices have inconsistent or incomplete {label} metadata."
            )

    first = datasets[0][1]
    expected_rows, expected_columns = int(first.Rows), int(first.Columns)
    if expected_rows < 1 or expected_columns < 1:
        raise ValueError("DICOM Rows and Columns must be positive.")
    voxel_count = len(datasets) * expected_rows * expected_columns
    if voxel_count > MAX_VOLUME_VOXELS:
        raise ValueError(
            f"DICOM series contains {voxel_count:,} voxels; the safety limit is "
            f"{MAX_VOLUME_VOXELS:,}."
        )
    pixel_attributes = (
        "SamplesPerPixel", "PhotometricInterpretation", "BitsAllocated",
        "BitsStored", "HighBit", "PixelRepresentation",
    )
    reference_pixel_spec = tuple(getattr(first, name, None) for name in pixel_attributes)
    if any(value is None for value in reference_pixel_spec):
        raise ValueError("DICOM pixel representation metadata is incomplete.")
    if reference_pixel_spec[0] != 1 or reference_pixel_spec[1] not in {"MONOCHROME1", "MONOCHROME2"}:
        raise ValueError("Only single-channel monochrome DICOM pixel data is supported.")
    bits_allocated, bits_stored, high_bit, pixel_representation = (
        reference_pixel_spec[2], reference_pixel_spec[3],
        reference_pixel_spec[4], reference_pixel_spec[5],
    )
    if (
        bits_allocated not in {8, 16, 32}
        or not isinstance(bits_stored, int)
        or not 1 <= bits_stored <= bits_allocated
        or high_bit != bits_stored - 1
        or pixel_representation not in {0, 1}
    ):
        raise ValueError("DICOM pixel bit-depth or representation metadata is unsupported.")
    for _, ds in datasets:
        pixel_spec = tuple(getattr(ds, name, None) for name in pixel_attributes)
        if pixel_spec != reference_pixel_spec:
            raise ValueError("DICOM slices have inconsistent pixel representation metadata.")

    if any(not hasattr(ds, "PixelSpacing") for _, ds in datasets):
        raise ValueError("Every DICOM slice must provide PixelSpacing for physical geometry.")
    first_spacing = _dicom_vector(first.PixelSpacing, "PixelSpacing", 2)
    if np.any(first_spacing <= 0):
        raise ValueError("DICOM PixelSpacing values must be positive.")

    has_orientation = [hasattr(ds, "ImageOrientationPatient") for _, ds in datasets]
    has_position = [hasattr(ds, "ImagePositionPatient") for _, ds in datasets]
    geometry_available = all(has_orientation) and all(has_position)
    if any(has_orientation) or any(has_position):
        if not geometry_available:
            raise ValueError(
                "DICOM spatial metadata is incomplete: every slice must provide both "
                "ImageOrientationPatient and ImagePositionPatient."
            )

    row_direction = column_direction = normal = None
    positions: list[np.ndarray] = []
    if geometry_available:
        reference_orientation = _dicom_vector(
            first.ImageOrientationPatient, "ImageOrientationPatient", 6
        )
        for _, ds in datasets:
            orientation = _dicom_vector(
                ds.ImageOrientationPatient, "ImageOrientationPatient", 6
            )
            if not np.allclose(orientation, reference_orientation, rtol=0.0, atol=1e-4):
                raise ValueError("DICOM slices have inconsistent ImageOrientationPatient values.")
            spacing = _dicom_vector(
                getattr(ds, "PixelSpacing", ()), "PixelSpacing", 2
            )
            if not np.allclose(spacing, first_spacing, rtol=0.0, atol=1e-4):
                raise ValueError("DICOM slices have inconsistent PixelSpacing values.")
            positions.append(_dicom_vector(ds.ImagePositionPatient, "ImagePositionPatient", 3))

        # DICOM's first direction cosine follows increasing column index (x);
        # the second follows increasing row index (y).
        column_direction = reference_orientation[:3]
        row_direction = reference_orientation[3:]
        column_norm = float(np.linalg.norm(column_direction))
        row_norm = float(np.linalg.norm(row_direction))
        if not np.isclose(column_norm, 1.0, atol=1e-3) or not np.isclose(row_norm, 1.0, atol=1e-3):
            raise ValueError("DICOM orientation direction cosines must be unit vectors.")
        column_direction = column_direction / column_norm
        row_direction = row_direction / row_norm
        if not np.isclose(float(np.dot(column_direction, row_direction)), 0.0, atol=1e-3):
            raise ValueError("DICOM row and column directions are not orthogonal.")
        normal = np.cross(column_direction, row_direction)
        normal_norm = float(np.linalg.norm(normal))
        if normal_norm <= 1e-8:
            raise ValueError("DICOM slice normal could not be determined.")
        normal = normal / normal_norm
        projections = np.asarray([float(np.dot(position, normal)) for position in positions])
        order = np.argsort(projections, kind="stable")
        sorted_projections = projections[order]
        if len(sorted_projections) > 1:
            differences = np.diff(sorted_projections)
            if np.any(differences <= 1e-5):
                raise ValueError("DICOM series contains duplicate or indistinguishable slice positions.")
            z_spacing = float(np.median(differences))
            tolerance = max(0.01, z_spacing * 0.01)
            if np.any(np.abs(differences - z_spacing) > tolerance):
                raise ValueError(
                    "DICOM slice positions are non-uniform; a single regular 3D voxel grid "
                    "cannot represent this series safely."
                )
        else:
            z_spacing = float(getattr(first, "SpacingBetweenSlices",
                                      getattr(first, "SliceThickness", 1.0)))
        datasets = [datasets[int(index)] for index in order]
        sorted_positions = [positions[int(index)] for index in order]
        origin = sorted_positions[0]
        if len(sorted_positions) > 1:
            position_steps = np.diff(np.asarray(sorted_positions), axis=0)
            mean_step = np.mean(position_steps, axis=0)
            if not np.isfinite(mean_step).all() or np.linalg.norm(mean_step) <= 1e-5:
                raise ValueError("DICOM slice displacement vector is invalid.")
            step_tolerance = max(0.01, float(np.linalg.norm(mean_step)) * 0.01)
            if np.any(np.linalg.norm(position_steps - mean_step, axis=1) > step_tolerance):
                raise ValueError(
                    "DICOM slice positions have inconsistent in-plane displacement; "
                    "a single affine 3D grid cannot represent this series safely."
                )
            slice_step_lps = mean_step
            z_spacing = float(np.linalg.norm(slice_step_lps))
        else:
            slice_step_lps = normal * z_spacing
    else:
        datasets.sort(key=lambda item: int(getattr(item[1], "InstanceNumber", 0)))
        z_spacing = float(getattr(first, "SpacingBetweenSlices",
                                  getattr(first, "SliceThickness", 1.0)))
        origin = None
        slice_step_lps = None

    if not np.isfinite(z_spacing) or z_spacing <= 0:
        raise ValueError("DICOM slice spacing must be a positive finite value.")

    arrays = []
    for file_path, ds in datasets:
        if int(ds.Rows) != expected_rows or int(ds.Columns) != expected_columns:
            raise ValueError("DICOM slices have inconsistent Rows or Columns.")
        pixels = np.asarray(ds.pixel_array, dtype=np.float32)
        if pixels.ndim != 2 or pixels.shape != (expected_rows, expected_columns):
            raise ValueError(f"Unsupported DICOM pixel array shape in {file_path.name}.")
        slope = float(getattr(ds, "RescaleSlope", 1.0))
        intercept = float(getattr(ds, "RescaleIntercept", 0.0))
        if not np.isfinite(slope) or not np.isfinite(intercept):
            raise ValueError("DICOM rescale slope/intercept must be finite.")
        pixels = pixels * slope + intercept
        arrays.append(pixels)

    volume = np.stack(arrays, axis=0)
    if str(getattr(datasets[0][1], "PhotometricInterpretation", "")).strip().upper() == "MONOCHROME1":
        # Use one intensity range for the whole series so slice-to-slice
        # polarity normalization does not introduce artificial intensity jumps.
        pixel_min = float(np.min(volume))
        pixel_max = float(np.max(volume))
        volume = (pixel_min + pixel_max) - volume
    row_spacing, column_spacing = float(first_spacing[0]), float(first_spacing[1])
    affine = None
    if geometry_available and len(datasets) > 0:
        affine = np.eye(4, dtype=float)
        affine[:3, 0] = column_direction * column_spacing
        affine[:3, 1] = row_direction * row_spacing
        affine[:3, 2] = slice_step_lps
        affine[:3, 3] = origin
        # DICOM patient coordinates are LPS; NIfTI world coordinates are RAS.
        # Convert once here so geometry comparisons across formats are meaningful.
        lps_to_ras = np.diag([-1.0, -1.0, 1.0, 1.0])
        affine = lps_to_ras @ affine

    ds0 = datasets[0][1]
    return MRIVolume(
        data=volume,
        spacing_mm=(
            float(np.linalg.norm(slice_step_lps)) if slice_step_lps is not None else z_spacing,
            row_spacing, column_spacing,
        ),
        source=str(root),
        modality=str(getattr(ds0, "Modality", "MRI")),
        affine=affine,
        metadata={
            "format": "DICOM",
            "slices_loaded": int(volume.shape[0]),
            "series_instance_uid": str(getattr(ds0, "SeriesInstanceUID", "")),
            "series_description": str(getattr(ds0, "SeriesDescription", "")),
            "patient_id_present": bool(getattr(ds0, "PatientID", "")),
            "image_orientation_patient": (
                list(ds0.ImageOrientationPatient) if geometry_available else None
            ),
            "spatial_geometry_verified": geometry_available,
            "photometric_interpretation": str(getattr(ds0, "PhotometricInterpretation", "")),
            "slice_displacement_mm": (
                float(np.linalg.norm(slice_step_lps)) if slice_step_lps is not None else None
            ),
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
