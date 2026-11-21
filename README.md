# Brain MRI 3D Reconstruction

A research-oriented Python application for loading 3D brain MRI volumes from **NIfTI** files or conventional **single-frame DICOM series**, checking spatial metadata, and exploring 2D/3D intensity views.

> **Important:** this project is an image viewer/reconstruction prototype. It does not contain a validated tumor detector or tumor segmentation model. Intensity thresholds and isosurfaces are not diagnoses, anatomical masks, or tumor boundaries.

## Capabilities

- Load 3D NIfTI volumes (`.nii`, `.nii.gz`) and conventional single-frame DICOM series.
- Load a DICOM series from a directory in the Python API/CLI, or from a ZIP archive in the Streamlit app.
- Reject mixed DICOM SeriesInstanceUIDs and several inconsistent or unsupported series configurations.
- Check multi-sequence array shape, spatial affine, orientation, and voxel spacing before enabling synchronized voxel-index slice comparison.
- Disable synchronized comparison when geometry is missing or does not match; the application does not silently register or resample images.
- Inspect three orthogonal **array-axis** slice views. For oblique acquisitions, these views are not automatically anatomical axial/coronal/sagittal planes.
- Explore 3D intensity volume rendering and intensity-derived isosurfaces.
- Preserve NIfTI affine metadata after canonical reorientation and convert DICOM patient coordinates from LPS to RAS when complete spatial geometry is available.
- Use the full affine for physical-space 3D display coordinates when available; otherwise display relative axes without claiming patient-space orientation.
- Apply bounded ZIP extraction checks for path traversal, symlinks, duplicate normalized paths, excessive entry counts, and oversized/high-ratio archives.

## Project layout

```text
MRI/
├── app.py
├── main.py
├── requirements.txt
├── src/
│   ├── volume_io.py
│   ├── multimodal.py
│   ├── preprocessing.py
│   ├── reconstruction.py
│   ├── segmentation.py
│   └── main.py
├── tests/
└── .github/workflows/ci.yml
```

## Setup (Windows PowerShell)

The CI workflow currently uses Python 3.11.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks environment activation, call the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run the web application

```powershell
streamlit run app.py
```

Upload one or more NIfTI files or ZIP archives, with each ZIP containing one DICOM series. Assign the correct sequence label to each upload. Filename-based sequence hints are suggestions only and can be overridden in the interface.

## Run from the command line

```powershell
python main.py "D:\MRI\patient01"
python main.py "D:\MRI\patient01.nii.gz" --output volume.html
```

## Local engineering validation (privacy-preserving)

Use the local validation CLI on one DICOM series directory or one 3D NIfTI file.
It keeps the scan on your computer and writes a summary without source paths,
patient identifiers, DICOM UIDs, series descriptions, origin coordinates, or image data.

```powershell
python scripts/validate_mri.py "D:\MRI\deidentified_series" --output "D:\MRI\validation_report.md"
python scripts/validate_mri.py "D:\MRI\scan.nii.gz" --format json --output "D:\MRI\validation_report.json"
```

Compare slice order, orientation, and spacing with a trusted independent viewer.
The script cannot confirm expected slice completeness without a reference.
See [the Windows guide](docs/local_mri_validation.md). This is not diagnosis or
clinical validation; do not publish scan-derived images or HTML.

## Run tests

```powershell
python -m pytest -q
```

The automated suite uses generated synthetic DICOM fixtures and temporary synthetic NIfTI files. It also exercises ZIP safety checks and headless Streamlit upload paths for NIfTI and DICOM ZIP inputs. These tests verify selected software behaviors on controlled fixtures; they are **not tests on real patient scans**.

See [the validation report](reports/validation_report.md) for the tested areas, CI run references, known gaps, and the scope of any future real-data validation.

## Validation status

- **Automated synthetic-fixture tests:** run in GitHub Actions and cover selected NIfTI, DICOM geometry/ordering, multi-sequence geometry checks, rendering, ZIP security, and Streamlit upload behavior.
- **Real-world DICOM validation:** not performed for this release. No real clinical DICOM series has been processed end to end as part of this repository workflow.
- **Clinical validation:** not performed. Passing CI does not establish clinical accuracy, diagnostic performance, or suitability for patient care.

## Important limitations

- Geometry compatibility is a metadata/grid check, not proof of clinical registration quality or anatomical correspondence.
- Multi-sequence registration, resampling, voxel-wise fusion, and overlays are not implemented.
- DICOM support targets conventional single-frame series. Enhanced multi-frame DICOM, complex multi-series studies, localizer filtering, and broader vendor-specific edge cases need additional validation.
- DICOM files without complete orientation/position metadata may be loaded without a patient-space affine; such volumes cannot pass the strict multi-sequence geometry compatibility check.
- DICOM parsing currently skips files that fail parsing when they do not use a `.dcm` or `.dicom` extension. Use a clean series directory containing the intended image instances.
- The isosurface is derived from intensity levels only. It is not a brain extraction mask, tissue segmentation, or tumor boundary.
- 4D/time-series NIfTI is not supported.
- Large volumes are downsampled for 3D display; source arrays are retained for slice inspection.
- Tumor segmentation is intentionally unavailable until suitable labeled data, expert reference masks, trained model weights, and patient-separated evaluation are provided.

## Disclaimer

Research and educational use only. Not intended for diagnosis, treatment decisions, or clinical use. De-identify medical data before sharing or uploading it.
