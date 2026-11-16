"""Command-line entry point for real MRI volume inspection."""

from __future__ import annotations

import argparse

from src.reconstruction import make_volume_figure
from src.volume_io import load_volume


def main() -> None:
    parser = argparse.ArgumentParser(description="Load and inspect a DICOM series or NIfTI MRI volume.")
    parser.add_argument("input", help="Path to a DICOM directory, .nii file, or .nii.gz file")
    parser.add_argument("--output", help="Optional path for an interactive HTML volume view")
    args = parser.parse_args()

    volume = load_volume(args.input)
    print(f"Loaded: {volume.source}")
    print(f"Format: {volume.metadata.get('format', 'unknown')}")
    print(f"Shape (z, y, x): {volume.data.shape}")
    print(f"Spacing (z, y, x) mm: {volume.spacing_mm}")
    print("This is an MRI intensity volume, not a tumor prediction.")
    if args.output:
        make_volume_figure(volume).write_html(args.output, include_plotlyjs="cdn")
        print(f"Interactive 3D view saved to: {args.output}")


if __name__ == "__main__":
    main()
