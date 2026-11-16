# Brain MRI 3D Reconstruction

A research-oriented Python application for loading real brain MRI data and reconstructing spatially-aware 3D views from **DICOM series** or **NIfTI** files.

> **Important:** this project visualizes MRI intensities. It does not include a validated tumor detector or tumor segmentation model. Intensity thresholds and isosurfaces must never be interpreted as tumor diagnoses or anatomical masks.

## Capabilities

- Load 3D NIfTI volumes (`.nii`, `.nii.gz`).
- Load one conventional single-frame DICOM series from a directory or ZIP archive.
- Reject mixed DICOM series rather than accidentally stacking unrelated acquisitions.
- Upload multiple sequences and label them as FLAIR, T1, T1ce, T2, or Other.
- Check multi-sequence array shape, spatial affine, orientation, and voxel spacing before synchronized slice comparison.
- Enable synchronized axial slice comparison only when every uploaded volume passes strict geometry checks.
- Warn and disable voxel-index comparison when geometry is mismatched or unavailable.
- Inspect the three orthogonal array-axis slice planes for each sequence. These are not automatically relabeled as anatomical planes for oblique DICOM acquisitions.
- Explore physical-space 3D intensity volume rendering and exploratory intensity isosurfaces.
- Preserve NIfTI orientation via canonical reorientation and voxel spacing metadata; convert DICOM patient coordinates from LPS to RAS for a shared world-coordinate convention.
- Use the full spatial affine (orientation, origin, and voxel scale) for 3D display coordinates when geometry is available.

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

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use the environment's Python directly:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run the web application

```powershell
streamlit run app.py
```

Upload one or more NIfTI volumes or ZIP files, with each ZIP containing one DICOM series. Assign the correct sequence label to each upload. Filename hints are only suggestions and can be overridden.

## Run from the command line

```powershell
python main.py "D:\MRI\patient01"
python main.py "D:\MRI\patient01.nii.gz" --output volume.html
```

## Tests

```powershell
python -m pytest -q
```

Tests use synthetic arrays and temporary NIfTI fixtures to validate software behavior. They are not clinical validation and do not establish image reconstruction accuracy on clinical scans.

## Important limitations and next research stage

- Geometry compatibility is verified using shape, affine, orientation (encoded in affine), and voxel spacing. Missing affine metadata is treated as unverified.
- Matching metadata is a necessary software check, not proof of clinical registration quality. The sample BraTS 2021 subject inspected during development had matching grids and affine metadata across FLAIR, T1, T1ce, and T2.
- Multi-sequence registration, resampling, voxel-wise fusion, and overlays are not implemented. No registration or resampling is performed automatically.
- DICOM support targets conventional single-frame series with consistent non-empty SeriesInstanceUID, PixelSpacing, and supported acquisition metadata. Enhanced multi-frame DICOM, complex multi-series studies, and localizer filtering need further validation.
- The isosurface is derived from intensity levels only. It is not a brain extraction mask, tissue segmentation, or tumor boundary.
- 4D/time-series NIfTI is not supported.
- Large volumes are downsampled for 3D display; source volumes remain unchanged for slice inspection.
- Tumor segmentation is disabled until labeled images, expert masks, trained weights, and patient-separated evaluation are available. Unlabeled scans can support exploratory quality review or anomaly scoring, not supervised tumor diagnosis.

## Disclaimer

Research and educational use only. Not intended for diagnosis, treatment decisions, or clinical use. De-identify medical data before sharing or uploading it.
