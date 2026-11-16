# Brain MRI 3D Reconstruction

A research-oriented Python application for loading real brain MRI data and reconstructing a spatially-aware 3D volume from **DICOM series** or **NIfTI** files.

> **Important:** this repository currently implements image loading, volume handling, slice viewing, and 3D intensity visualization. It does **not** provide a validated tumor detector or tumor segmentation model. Bright regions and intensity thresholds must never be interpreted as tumor diagnoses.

## Current capabilities

- Load a DICOM series from a folder (including nested folders) or a ZIP archive in the web app.
- Load NIfTI `.nii` and `.nii.gz` volumes.
- Preserve voxel spacing and NIfTI orientation information; sort DICOM slices using patient-space geometry when available.
- Inspect axial, coronal, and sagittal slices.
- Explore a downsampled 3D volume rendering without inventing segmentation masks.
- Run automated tests and CI.

## Project layout

```text
MRI/
├── app.py
├── main.py
├── requirements.txt
├── src/
│   ├── volume_io.py
│   ├── preprocessing.py
│   ├── reconstruction.py
│   ├── segmentation.py
│   └── main.py
├── tests/
└── .github/workflows/ci.yml
```

## Setup (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run the commands without activating the environment:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run the web application

```powershell
streamlit run app.py
```

Upload one NIfTI file (`.nii` / `.nii.gz`) or a ZIP containing a DICOM series. The app displays volume dimensions, voxel spacing, three orthogonal slice views, and an interactive 3D intensity rendering.

## Run from the command line

For a NIfTI file or a directory containing DICOM files:

```powershell
python main.py "D:\MRI\patient01"
python main.py "D:\MRI\patient01.nii.gz" --output volume.html
```

The command-line tool prints the volume shape and spacing. If `--output` is supplied, it writes an interactive HTML volume view.

## Tests

```powershell
python -m pytest -q
```

Tests use synthetic arrays and a temporary NIfTI fixture to validate software behavior only; they are not clinical validation.

## Tumor detection status and next research stage

Tumor detection/segmentation is deliberately unavailable until a suitable labeled dataset, segmentation masks, a documented training procedure, and patient-level evaluation are supplied. The current `src/segmentation.py` raises an explicit error rather than generating misleading percentile-based pseudo-masks.

The previously mentioned unlabeled patient scans can support data-quality review and exploratory anomaly scoring, but cannot by themselves establish supervised tumor labels or diagnostic accuracy. Any future model must be evaluated on patient-separated data and clearly labeled as research software, not a medical device.

## Supported inputs and limitations

- DICOM: conventional single-frame image series with pixel data. Enhanced multi-frame DICOM, localizer filtering, and complex multi-series studies need additional validation.
- NIfTI: 3D scalar volumes. 4D/time-series and multi-modal registration are not yet implemented.
- Large volumes are downsampled for interactive 3D display; the source volume remains unchanged for slice inspection.
- De-identify medical data before sharing or uploading it.

## Disclaimer

This software is for research and educational use only. It is not intended for diagnosis, treatment decisions, or clinical use.
