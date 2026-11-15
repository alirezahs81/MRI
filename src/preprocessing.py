"""
MRI Preprocessing Module.
Handles loading, intensity normalization, and noise reduction for medical imaging data.
"""

import numpy as np
import cv2


class MRIPreprocessor:
    """Preprocesses raw MRI scan slices or volumes."""

    def __init__(self, target_size: tuple = (256, 256)):
        self.target_size = target_size

    def resize_image(self, image: np.ndarray) -> np.ndarray:
        """Resize image to the target dimensions."""
        return cv2.resize(image, self.target_size, interpolation=cv2.INTER_CUBIC)

    def normalize_intensity(self, image: np.ndarray) -> np.ndarray:
        """Normalize pixel intensities to the range [0, 1]."""
        img_min = np.min(image)
        img_max = np.max(image)
        if img_max - img_min == 0:
            return image
        return (image - img_min) / (img_max - img_min)

    def denoise_image(self, image: np.ndarray) -> np.ndarray:
        """Apply Gaussian blur or non-local means for noise reduction."""
        # Ensure image is suitable for filtering (e.g. 8-bit or float)
        if image.dtype != np.float32 and image.dtype != np.float64:
            image = image.astype(np.float32)
        return cv2.GaussianBlur(image, (5, 5), 0)

    def process(self, image: np.ndarray) -> np.ndarray:
        """Execute full preprocessing pipeline on a single image slice."""
        resized = self.resize_image(image)
        normalized = self.normalize_intensity(resized)
        denoised = self.denoise_image(normalized)
        return denoised
