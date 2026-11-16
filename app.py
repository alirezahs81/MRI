"""Streamlit viewer for multiple MRI sequences supplied as NIfTI files or DICOM ZIPs."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from src.multimodal import check_geometry_compatibility
from src.reconstruction import make_isosurface_figure, make_slice_figure, make_volume_figure
from src.volume_io import load_volume


SEQUENCES = ("FLAIR", "T1", "T1ce", "T2", "Other")


def infer_sequence(filename: str) -> str:
    """Best-effort filename hint; users can always override it in the interface."""
    name = filename.lower().replace("-", "_").replace(" ", "_")
    for token, label in (("flair", "FLAIR"), ("t1ce", "T1ce"), ("t1_c", "T1ce"),
                         ("t1", "T1"), ("t2", "T2")):
        if token in name:
            return label
    return "Other"


def extract_dicom_zip(archive_path: Path, destination: Path) -> None:
    """Extract a ZIP only after checking every member stays inside destination."""
    destination_resolved = destination.resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if target != destination_resolved and destination_resolved not in target.parents:
                raise ValueError("ZIP archive contains an unsafe path.")
        archive.extractall(destination)


st.set_page_config(page_title="Brain MRI 3D Viewer", layout="wide")
st.title("Brain MRI — Multi-sequence 3D Viewer")
st.warning(
    "Research viewer only. Intensity rendering is not anatomical segmentation and does not detect or diagnose tumors."
)
st.write(
    "Upload one or more NIfTI volumes (.nii/.nii.gz) or ZIP archives containing one DICOM series each. "
    "Assign the correct sequence to every upload."
)
uploads = st.file_uploader(
    "MRI sequence files", type=["nii", "gz", "zip"], accept_multiple_files=True
)

if uploads:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        loaded = []
        for number, uploaded in enumerate(uploads):
            detected = infer_sequence(uploaded.name)
            with st.expander(f"Input {number + 1}: {uploaded.name}", expanded=True):
                default_index = SEQUENCES.index(detected)
                sequence = st.selectbox(
                    "Sequence label",
                    SEQUENCES,
                    index=default_index,
                    key=f"sequence_{number}_{uploaded.name}",
                )
            try:
                input_root = root / f"input_{number}"
                input_root.mkdir()
                lower_name = uploaded.name.lower()
                if lower_name.endswith(".nii") or lower_name.endswith(".nii.gz"):
                    input_path = input_root / uploaded.name
                    input_path.write_bytes(uploaded.getvalue())
                    volume = load_volume(input_path)
                elif lower_name.endswith(".zip"):
                    archive_path = input_root / "series.zip"
                    archive_path.write_bytes(uploaded.getvalue())
                    dicom_root = input_root / "dicom"
                    dicom_root.mkdir()
                    extract_dicom_zip(archive_path, dicom_root)
                    volume = load_volume(dicom_root)
                else:
                    raise ValueError("Unsupported file type.")
                loaded.append((sequence, uploaded.name, volume))
            except Exception as exc:
                st.error(f"{uploaded.name}: {exc}")

        if loaded:
            st.success(f"Loaded {len(loaded)} MRI sequence(s).")
            st.caption(
                "Geometry is checked before synchronized multi-sequence viewing. "
                "No registration or resampling is performed automatically."
            )

            if len(loaded) > 1:
                reference_sequence, reference_name, reference_volume = loaded[0]
                compatibility = []
                for sequence, filename, volume in loaded[1:]:
                    is_compatible, reason = check_geometry_compatibility(
                        reference_volume, volume
                    )
                    compatibility.append((sequence, filename, is_compatible, reason))

                if all(item[2] for item in compatibility):
                    st.success(
                        "All uploaded volumes have matching voxel grids and spatial affine "
                        "metadata. Synchronized slice comparison is enabled for this upload set."
                    )
                    axial_index = st.slider(
                        "Synchronized axial slice",
                        min_value=0,
                        max_value=reference_volume.data.shape[0] - 1,
                        value=(reference_volume.data.shape[0] - 1) // 2,
                        key="shared_axial_index",
                    )
                    comparison_columns = st.columns(min(len(loaded), 4))
                    for index, (sequence, filename, volume) in enumerate(loaded):
                        with comparison_columns[index % len(comparison_columns)]:
                            st.markdown(f"**{sequence}**")
                            st.caption(filename)
                            st.plotly_chart(
                                make_slice_figure(volume, "axial", axial_index),
                                use_container_width=True,
                                key=f"aligned_axial_{index}",
                            )
                else:
                    st.warning(
                        "Synchronized voxel-wise comparison is disabled because geometry "
                        "could not be verified for every uploaded sequence. Do not compare "
                        "the same voxel index across these images."
                    )
                    for sequence, filename, is_compatible, reason in compatibility:
                        status = "compatible with reference" if is_compatible else "not verified"
                        st.write(f"- {sequence} ({filename}): {status} — {reason}")
                    st.info(
                        "Use a validated registration/resampling workflow before overlays or "
                        "voxel-wise fusion. This viewer does not register images."
                    )

            for number, (sequence, filename, volume) in enumerate(loaded):
                with st.container(border=True):
                    st.subheader(f"{sequence} — {filename}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Slices (Z)", volume.data.shape[0])
                    c2.metric("Rows (Y)", volume.data.shape[1])
                    c3.metric("Columns (X)", volume.data.shape[2])
                    st.caption(
                        f"Voxel spacing (Z, Y, X): {volume.spacing_mm} mm · "
                        f"Format: {volume.metadata.get('format')} · "
                        f"Series: {volume.metadata.get('series_description') or 'not provided'}"
                    )
                    st.markdown("**Orthogonal slices**")
                    columns = st.columns(3)
                    for column, plane, axis in zip(
                        columns, ("axial", "coronal", "sagittal"), (0, 1, 2)
                    ):
                        with column:
                            maximum = volume.data.shape[axis] - 1
                            index = st.slider(
                                f"{plane.title()} index",
                                0,
                                maximum,
                                maximum // 2,
                                key=f"{number}_{plane}_index",
                            )
                            st.plotly_chart(
                                make_slice_figure(volume, plane, index),
                                use_container_width=True,
                            )
                    st.markdown("**3D intensity rendering**")
                    st.plotly_chart(make_volume_figure(volume), use_container_width=True)
                    st.markdown("**Exploratory isosurface**")
                    st.caption(
                        "Surface levels are based on image intensity only; they are not a brain mask or tumor boundary."
                    )
                    st.plotly_chart(make_isosurface_figure(volume), use_container_width=True)
