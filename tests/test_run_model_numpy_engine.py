import copy

import numpy as np
import xarray as xr

from benchmarks.benchmark_run_model import (
    assert_equivalent_outputs,
    build_initialized_simulation,
)
from sarra_py import run_model, run_waterbalance_model


def _run_pair(model_func, duration=12, width=4, height=3):
    base, param_variety, param_itk, param_soil = build_initialized_simulation(
        duration=duration,
        width=width,
        height=height,
    )

    legacy = model_func(
        copy.deepcopy(param_variety),
        copy.deepcopy(param_itk),
        copy.deepcopy(param_soil),
        base.copy(deep=True),
        duration,
        engine="xarray",
        progress=False,
    )
    fast = model_func(
        copy.deepcopy(param_variety),
        copy.deepcopy(param_itk),
        copy.deepcopy(param_soil),
        base.copy(deep=True),
        duration,
        engine="numpy",
        progress=False,
    )
    return legacy, fast


def test_run_model_numpy_engine_matches_xarray_engine():
    legacy, fast = _run_pair(run_model)

    assert isinstance(fast, xr.Dataset)
    assert_equivalent_outputs(legacy, fast)


def test_run_waterbalance_numpy_engine_matches_xarray_engine():
    legacy, fast = _run_pair(run_waterbalance_model)

    assert isinstance(fast, xr.Dataset)
    assert_equivalent_outputs(legacy, fast)


def test_run_model_default_call_still_returns_dataset_with_same_api_shape():
    duration = 8
    base, param_variety, param_itk, param_soil = build_initialized_simulation(
        duration=duration,
        width=3,
        height=2,
    )

    result = run_model(param_variety, param_itk, param_soil, base, duration, progress=False)

    assert isinstance(result, xr.Dataset)
    assert dict(result.sizes) == dict(base.sizes)
    assert set(result.coords) == set(base.coords)
    assert set(result.data_vars) == set(base.data_vars)
    np.testing.assert_array_equal(result.coords["time"], base.coords["time"])
