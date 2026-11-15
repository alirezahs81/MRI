"""
Main Pipeline Runner for MRI Brain Tumor Detection & 3D Reconstruction.
"""

import numpy as np
from src.preprocessing import MRIPreprocessor
from src.segmentation import TumorSegmenter
from src.reconstruction import TumorReconstructor3D


def run_pipeline():
    print("=== Starting Brain Tumor MRI & 3D Pipeline ===")

    # 1. Simulate a 3D MRI volume stack (Depth=10 slices, 256x256 resolution)
    print("[1/3] Generating/Loading sample MRI volume...")
    mock_volume = np.random.rand(10, 256, 256)

    # 2. Preprocess slices
    print("[2/3] Preprocessing MRI slices...")
    preprocessor = MRIPreprocessor(target_size=(256, 256))
    processed_slices = [preprocessor.process(slice_) for slice_ in mock_volume]

    # 3. Tumor Segmentation
    print("[3/3] Performing Tumor Segmentation & 3D Reconstruction...")
    segmenter = TumorSegmenter()
    masks = [segmenter.predict_mask(s) for s in processed_slices]
    mask_stack = np.array(masks)

    # 4. 3D Reconstruction
    reconstructor = TumorReconstructor3D()
    fig = reconstructor.render_plotly_3d(mask_stack)

    print("Pipeline executed successfully! 3D Model generated.")
    return fig


if __name__ == "__main__":
    run_pipeline()
