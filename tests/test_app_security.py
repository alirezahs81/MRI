"""Security tests for bounded ZIP extraction used by the Streamlit upload flow."""

import zipfile

import pytest

from app import extract_dicom_zip


def test_extract_dicom_zip_extracts_safe_members(tmp_path):
    archive_path = tmp_path / "series.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("nested/slice.dcm", b"dicom-data")
    destination = tmp_path / "out"
    extract_dicom_zip(archive_path, destination)
    assert (destination / "nested" / "slice.dcm").read_bytes() == b"dicom-data"


def test_extract_dicom_zip_rejects_parent_traversal(tmp_path):
    archive_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", b"bad")
    with pytest.raises(ValueError, match="unsafe path"):
        extract_dicom_zip(archive_path, tmp_path / "out")


def test_extract_dicom_zip_rejects_windows_style_traversal(tmp_path):
    archive_path = tmp_path / "unsafe-windows.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(r"..\\outside.txt", b"bad")
    with pytest.raises(ValueError, match="unsafe path"):
        extract_dicom_zip(archive_path, tmp_path / "out")


def test_extract_dicom_zip_rejects_too_many_entries(tmp_path, monkeypatch):
    archive_path = tmp_path / "many.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("one.dcm", b"1")
        archive.writestr("two.dcm", b"2")
    monkeypatch.setattr("app.MAX_ZIP_MEMBERS", 1)
    with pytest.raises(ValueError, match="too many entries"):
        extract_dicom_zip(archive_path, tmp_path / "out")



def test_extract_dicom_zip_rejects_duplicate_normalized_paths(tmp_path):
    archive_path = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("nested/slice.dcm", b"first")
        archive.writestr("nested//slice.dcm", b"second")
    with pytest.raises(ValueError, match="duplicate normalized paths"):
        extract_dicom_zip(archive_path, tmp_path / "out")
