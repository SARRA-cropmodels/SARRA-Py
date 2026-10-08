import datetime as dt

import numpy as np

from benchmarks.benchmark_helpers import (
    build_recent_notebook_input,
    reference_calc_day_length_raster_fast,
    run_helper_benchmark,
)
from sarra_py import calc_day_length_raster_fast
from sarra_py.data_preparation import _cached_day_length_matrix


def test_cached_day_length_raster_matches_previous_helper():
    data, date_start = build_recent_notebook_input(duration=12, width=4, height=3)
    reference = reference_calc_day_length_raster_fast(data.copy(deep=True), date_start, 12)
    _cached_day_length_matrix.cache_clear()
    candidate = calc_day_length_raster_fast(data.copy(deep=True), date_start, 12)

    assert reference["dureeDuJour"].dims == candidate["dureeDuJour"].dims
    assert reference["dureeDuJour"].attrs == candidate["dureeDuJour"].attrs
    assert set(reference["dureeDuJour"].coords) == set(candidate["dureeDuJour"].coords)
    for coord_name in reference["dureeDuJour"].coords:
        np.testing.assert_array_equal(
            reference["dureeDuJour"].coords[coord_name],
            candidate["dureeDuJour"].coords[coord_name],
        )
    np.testing.assert_allclose(
        reference["dureeDuJour"].values,
        candidate["dureeDuJour"].values,
        rtol=1e-5,
        atol=1e-5,
        equal_nan=True,
    )


def test_cached_day_length_raster_reuses_same_day_latitude_matrix():
    data, date_start = build_recent_notebook_input(duration=8, width=3, height=2)
    _cached_day_length_matrix.cache_clear()

    calc_day_length_raster_fast(data.copy(deep=True), date_start, 8)
    first_info = _cached_day_length_matrix.cache_info()
    calc_day_length_raster_fast(data.copy(deep=True), dt.date(2023, 4, 1), 8)
    second_info = _cached_day_length_matrix.cache_info()

    assert first_info.misses == 1
    assert second_info.hits == first_info.hits + 1


def test_helper_benchmark_smoke_without_model():
    result = run_helper_benchmark(
        duration=8,
        width=3,
        height=2,
        scenario_count=2,
        include_model=False,
        check=True,
    )

    assert result["before"]["prepare_seconds"] >= 0
    assert result["after"]["prepare_seconds"] >= 0
    assert result["speedup"]["calc_day_length_raster_fast_seconds"] > 0
