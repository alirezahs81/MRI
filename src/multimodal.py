"""Strict geometry checks for voxel-wise multi-sequence MRI viewing."""

from __future__ import annotations

import numpy as np

from src.volume_io import MRIVolume


def check_geometry_compatibility(
    reference: MRIVolume,
    candidate: MRIVolume,
    *,
    atol: float = 1e-3,
) -> tuple[bool, str]:
    """Return whether two volumes can safely share voxel indices.

    Compatibility requires identical array shape and matching NIfTI world
    affine matrices. Missing affine metadata is treated as unverified, not
    compatible. This function does not perform image registration.
    """
    if reference.data.shape != candidate.data.shape:
        return (
            False,
            f"Shape mismatch: {reference.data.shape} vs {candidate.data.shape}.",
        )

    if reference.affine is None or candidate.affine is None:
        return (
            False,
            "A complete spatial affine is unavailable for at least one volume; "
            "voxel-wise alignment cannot be verified.",
        )

    reference_affine = np.asarray(reference.affine, dtype=float)
    candidate_affine = np.asarray(candidate.affine, dtype=float)
    if (
        reference_affine.shape != (4, 4)
        or candidate_affine.shape != (4, 4)
        or not np.isfinite(reference_affine).all()
        or not np.isfinite(candidate_affine).all()
    ):
        return False, "Invalid spatial affine metadata."

    if not np.allclose(reference_affine, candidate_affine, rtol=0.0, atol=atol):
        return False, "Spatial affine/orientation mismatch."

    if not np.allclose(reference.spacing_mm, candidate.spacing_mm, rtol=0.0, atol=atol):
        return False, "Voxel spacing mismatch."

    return True, "Matching shape, affine, orientation, and voxel spacing."
