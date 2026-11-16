"""Explicit guard for the not-yet-implemented, unvalidated tumor model."""


class ModelNotAvailableError(RuntimeError):
    """Raised when a validated tumor segmentation model has not been configured."""


class TumorSegmenter:
    """Placeholder API that refuses to fabricate tumor masks from image intensity."""

    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = model_path
        self.is_loaded = False

    def load_model(self) -> None:
        raise ModelNotAvailableError(
            "No validated tumor segmentation model is included. Supply labeled training data, "
            "trained weights, and independent patient-level evaluation before enabling inference."
        )

    def predict_mask(self, image_slice):
        raise ModelNotAvailableError(
            "Tumor segmentation is unavailable. Intensity thresholding is not a valid tumor detector."
        )
