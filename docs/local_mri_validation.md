# Local MRI validation (Windows PowerShell)

After installing the project requirements, run a local engineering check on one
DICOM series folder or one 3D NIfTI file. The MRI data stays on your computer;
only the small report is written to the output path you choose.

For a DICOM series, point to the folder containing one intended series:

```powershell
python scripts/validate_mri.py "D:\MRI\deidentified_series" --output "D:\MRI\validation_report.md"
```

For NIfTI:

```powershell
python scripts/validate_mri.py "D:\MRI\scan.nii.gz" --output "D:\MRI\validation_report.md"
```

To create JSON instead:

```powershell
python scripts/validate_mri.py "D:\MRI\scan.nii.gz" --format json --output "D:\MRI\validation_report.json"
```

The report intentionally excludes input paths, filenames, patient identifiers,
DICOM UIDs, series descriptions, patient-origin coordinates, and image data.
It reports basic volume dimensions, spacing, and detectable geometry status.
It cannot determine whether all clinically expected slices are present because
the expected slice count is not generally encoded reliably in a single series.

**Manual review is still required:** open the same study in a trusted independent
medical-image viewer and compare slice order, orientation, and spacing. Do not
upload clinical data or generated scan-derived HTML to a public repository.
The tool is for engineering review only; it does not diagnose, segment, or
establish clinical validity.
