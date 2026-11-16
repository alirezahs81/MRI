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



def test_upload_limits_accept_safe_uploads():
    from types import SimpleNamespace
    from app import validate_upload_limits

    validate_upload_limits([SimpleNamespace(size=1024), SimpleNamespace(size=2048)])


def test_upload_limits_rejects_oversized_single_file(monkeypatch):
    from types import SimpleNamespace
    from app import validate_upload_limits

    monkeypatch.setattr("app.MAX_UPLOAD_FILE_BYTES", 100)
    with pytest.raises(ValueError, match="Each upload"):
        validate_upload_limits([SimpleNamespace(size=101)])


def test_upload_limits_rejects_excessive_combined_size(monkeypatch):
    from types import SimpleNamespace
    from app import validate_upload_limits

    monkeypatch.setattr("app.MAX_UPLOAD_FILE_BYTES", 100)
    monkeypatch.setattr("app.MAX_TOTAL_UPLOAD_BYTES", 150)
    with pytest.raises(ValueError, match="Combined uploads"):
        validate_upload_limits([SimpleNamespace(size=80), SimpleNamespace(size=80)])


def test_upload_limits_rejects_too_many_files(monkeypatch):
    from types import SimpleNamespace
    from app import validate_upload_limits

    monkeypatch.setattr("app.MAX_UPLOADS", 1)
    with pytest.raises(ValueError, match="Too many uploads"):
        validate_upload_limits([SimpleNamespace(size=1), SimpleNamespace(size=1)])
