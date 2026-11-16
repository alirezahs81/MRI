"""Streamlit interface for DICOM ZIP and NIfTI brain MRI volume viewing."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from src.reconstruction import make_slice_figure, make_volume_figure
from src.volume_io import load_volume


st.set_page_config(page_title="Brain MRI 3D Viewer", layout="wide")
st.title("Brain MRI — 3D Reconstruction Viewer")
st.warning(
    "Research viewer only. This app visualizes MRI intensities; it does not detect or diagnose tumors."
)
st.write("Upload a 3D NIfTI file or a ZIP archive containing one conventional DICOM series.")
upload = st.file_uploader("MRI input", type=["nii", "gz", "zip"])

if upload is not None:
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lower_name = upload.name.lower()
            if lower_name.endswith(".nii") or lower_name.endswith(".nii.gz"):
                input_path = root / upload.name
                input_path.write_bytes(upload.getvalue())
                volume = load_volume(input_path)
            elif lower_name.endswith(".zip"):
                archive_path = root / "dicom_series.zip"
                archive_path.write_bytes(upload.getvalue())
                dicom_root = root / "dicom"
                dicom_root.mkdir()
                with zipfile.ZipFile(archive_path) as archive:
                    for member in archive.infolist():
                        destination = (dicom_root / member.filename).resolve()
                        if dicom_root.resolve() not in destination.parents and destination != dicom_root.resolve():
                            raise ValueError("ZIP archive contains an unsafe path.")
                    archive.extractall(dicom_root)
                volume = load_volume(dicom_root)
            else:
                raise ValueError("Please upload a .nii, .nii.gz, or .zip file.")

        st.success("MRI volume loaded.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Slices (Z)", volume.data.shape[0])
        c2.metric("Rows (Y)", volume.data.shape[1])
        c3.metric("Columns (X)", volume.data.shape[2])
        st.caption(f"Voxel spacing (Z, Y, X): {volume.spacing_mm} mm · Source: {volume.metadata.get('format')}")

        st.subheader("Orthogonal slices")
        columns = st.columns(3)
        for column, plane, axis in zip(columns, ("axial", "coronal", "sagittal"), (0, 1, 2)):
            with column:
                maximum = volume.data.shape[axis] - 1
                index = st.slider(f"{plane.title()} index", 0, maximum, maximum // 2, key=f"{plane}_index")
                st.plotly_chart(make_slice_figure(volume, plane, index), use_container_width=True)

        st.subheader("3D intensity volume")
        st.plotly_chart(make_volume_figure(volume), use_container_width=True)
    except Exception as exc:
        st.error(f"Could not load or display this MRI input: {exc}")
