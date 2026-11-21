"""Local, privacy-preserving engineering checks for an MRI volume.

The report intentionally excludes source paths, patient identifiers, DICOM UIDs,
series descriptions, patient-space origin coordinates, and image data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from src.volume_io import load_volume


def validate_volume(volume: Any) -> dict[str, Any]:
    """Return a whitelisted, non-identifying summary of a loaded MRI volume."""
    data = np.asarray(volume.data)
    affine = None if volume.affine is None else np.asarray(volume.affine, dtype=float)
    affine_valid = bool(
        affine is not None
        and affine.shape == (4, 4)
        and np.isfinite(affine).all()
        and np.allclose(affine[3], [0.0, 0.0, 0.0, 1.0], atol=1e-8)
        and abs(float(np.linalg.det(affine[:3, :3]))) > 1e-8
    )
    orientation = None
    if affine_valid:
        # RAS direction labels only; never include the affine's origin/translation.
        import nibabel as nib

        orientation = "".join(nib.orientations.aff2axcodes(affine))

    geometry_verified = bool(volume.metadata.get("spatial_geometry_verified", False))
    warnings: list[str] = []
    if not affine_valid:
        warnings.append(
            "A valid patient-space affine is unavailable; confirm orientation in a trusted viewer."
        )
    if not geometry_verified and str(volume.metadata.get("format", "")).upper() == "DICOM":
        warnings.append(
            "DICOM spatial metadata was not fully verified; do not assume patient-space alignment."
        )
    warnings.append(
        "Compare slice order, orientation, and spacing with a trusted independent medical-image viewer."
    )
    warnings.append(
        "This engineering report is not a diagnosis, segmentation, or clinical validation."
    )

    return {
        "report_type": "local_mri_engineering_validation",
        "input_format": str(volume.metadata.get("format", "unknown")).upper(),
        "volume_shape_zyx": [int(v) for v in data.shape],
        "slice_count": int(data.shape[0]),
        "voxel_spacing_mm_zyx": [round(float(v), 6) for v in volume.spacing_mm],
        "voxel_values_finite": bool(np.isfinite(data).all()),
        "spatial_affine_present": affine is not None,
        "spatial_affine_valid": affine_valid,
        "spatial_geometry_verified": geometry_verified if str(
            volume.metadata.get("format", "")
        ).upper() == "DICOM" else affine_valid,
        "ras_axis_orientation": orientation,
        "warnings": warnings,
        "clinical_validation_performed": False,
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render a compact report containing only approved summary fields."""
    spacing = ", ".join(f"{value:g}" for value in report["voxel_spacing_mm_zyx"])
    shape = " × ".join(str(value) for value in report["volume_shape_zyx"])
    warnings = "\n".join(f"- {item}" for item in report["warnings"])
    orientation = report["ras_axis_orientation"] or "unknown"
    return (
        "# Local MRI Engineering Validation\n\n"
        "> Research/engineering checks only. Not for diagnosis or clinical use.\n\n"
        f"- Input format: {report['input_format']}\n"
        f"- Volume shape (z, y, x): {shape}\n"
        f"- Slice count: {report['slice_count']}\n"
        f"- Voxel spacing (z, y, x), mm: {spacing}\n"
        f"- Voxel values finite: {report['voxel_values_finite']}\n"
        f"- Spatial affine present/valid: {report['spatial_affine_present']} / "
        f"{report['spatial_affine_valid']}\n"
        f"- Geometry verified: {report['spatial_geometry_verified']}\n"
        f"- RAS axis orientation: {orientation}\n"
        f"- Clinical validation performed: No\n\n"
        "## Manual verification required\n\n"
        f"{warnings}\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Load one local MRI volume and write a privacy-preserving engineering report."
    )
    parser.add_argument("input", help="Local DICOM series directory or .nii/.nii.gz file")
    parser.add_argument("--output", default="mri_validation_report.md", help="Report output path")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args(argv)

    try:
        volume = load_volume(Path(args.input))
        report = validate_volume(volume)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        content = render_markdown(report) if args.format == "markdown" else json.dumps(
            report, indent=2, ensure_ascii=False
        )
        output.write_text(content + ("" if content.endswith("\n") else "\n"), encoding="utf-8")
    except Exception:
        # Avoid printing exception text: DICOM/NIfTI loaders may include local paths.
        parser.error(
            "Could not validate this input. Check that it is a supported, readable "
            "DICOM series directory or 3D NIfTI file; details are omitted to protect local paths."
        )
    print(f"Validation report written ({args.format}); input paths and patient metadata were not included.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
