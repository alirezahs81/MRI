"""
Unit tests for preprocessing and segmentation modules.
"""

import numpy as np
import pytest
from src.preprocessing import MRIPreprocessor
from src.segmentation import TumorSegmenter


def test_mri_preprocessor():
    preprocessor = MRIPreprocessor(target_size=(128, 128))
    dummy_image = np.random.randint(0, 255, (200, 200), dtype=np.uint8)

    processed = preprocessor.process(dummy_image)

    assert processed.shape == (128, 128)
    assert np.min(processed) >= 0.0
    assert np.max(processed) <= 1.0


def test_tumor_segmenter():
    segmenter = TumorSegmenter()
    dummy_slice = np.random.rand(128, 128)

    mask = segmenter.predict_mask(dummy_slice)

    assert mask.shape == (128, 128)
    assert set(np.unique(mask)).issubset({0, 1})
