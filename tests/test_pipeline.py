import numpy as np
import pytest

from src.preprocessing import normalize_intensity
from src.reconstruction import make_isosurface_figure, make_slice_figure, make_volume_figure
from src.segmentation import ModelNotAvailableError, TumorSegmenter
from src.volume_io import MRIVolume


def sample_volume():
    data = np.arange(12 * 16 * 20, dtype=np.float32).reshape(12, 16, 20)
    return MRIVolume(data=data, spacing_mm=(1.5, 1.0, 1.0), source="synthetic-test")


def test_normalize_intensity_preserves_shape_and_range():
    volume = np.arange(120, dtype=np.float32).reshape(2, 6, 10)
    normalized = normalize_intensity(volume, 0, 100)
    assert normalized.shape == volume.shape
    assert normalized.min() == pytest.approx(0.0)
    assert normalized.max() == pytest.approx(1.0)


def test_slice_figure_accepts_all_orthogonal_planes():
    volume = sample_volume()
    for plane, index in (("axial", 2), ("coronal", 3), ("sagittal", 4)):
        figure = make_slice_figure(volume, plane, index)
        assert len(figure.data) == 1


def test_slice_figure_rejects_invalid_index():
    with pytest.raises(IndexError):
        make_slice_figure(sample_volume(), "axial", 99)


def test_volume_figure_is_created_without_fake_masks():
    figure = make_volume_figure(sample_volume(), max_dimension=16)
    assert len(figure.data) == 1
    assert figure.data[0].type == "volume"


def test_isosurface_figure_uses_physical_coordinates_after_downsampling():
    figure = make_isosurface_figure(sample_volume(), max_dimension=16)
    assert len(figure.data) == 1
    assert figure.data[0].type == "isosurface"
    # The 20-voxel x-axis is sampled at stride 2 (0, 2, ..., 18 mm).
    assert float(np.max(figure.data[0].x)) == pytest.approx(18.0)


def test_segmentation_does_not_generate_pseudo_tumor_masks():
    segmenter = TumorSegmenter()
    with pytest.raises(ModelNotAvailableError):
        segmenter.predict_mask(np.ones((8, 8), dtype=np.float32))



def test_display_grid_uses_full_affine_orientation_and_origin():
    from src.reconstruction import _display_grid

    affine = np.array([
        [0.0, -2.0, 0.0, 10.0],
        [3.0, 0.0, 0.0, 20.0],
        [0.0, 0.0, 4.0, 30.0],
        [0.0, 0.0, 0.0, 1.0],
    ])
    volume = MRIVolume(
        data=np.zeros((8, 8, 8), dtype=np.float32),
        spacing_mm=(4.0, 3.0, 2.0),
        source="affine-test",
        affine=affine,
    )
    _, world_x, world_y, world_z = _display_grid(volume, max_dimension=8)
    assert world_x[3, 2, 1] == pytest.approx(6.0)
    assert world_y[3, 2, 1] == pytest.approx(23.0)
    assert world_z[3, 2, 1] == pytest.approx(42.0)
