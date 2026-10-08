import inspect

import pytest

from benchmarks.benchmark_exemple_12 import (
    EXEMPLE12_DATA,
    NOTEBOOK_PATH,
    NOTEBOOK_VALUE_VARIABLES,
    SUMMARY_VARIABLES,
    run_realistic_benchmark,
)


pytest.importorskip("rioxarray")
pytest.importorskip("netCDF4")


DATA_AVAILABLE = (
    NOTEBOOK_PATH.exists()
    and (EXEMPLE12_DATA / "rainfall").exists()
    and (EXEMPLE12_DATA / "tmax").exists()
    and (EXEMPLE12_DATA / "tmin").exists()
    and (EXEMPLE12_DATA / "solar_radiation_flux").exists()
)


def test_exemple12_public_notebook_api_symbols_still_importable():
    from sarra_py import (  # noqa: PLC0415
        calc_day_length_raster_fast,
        calculate_once_daily_thermal_time,
        initialize_default_irrigation,
        initialize_simulation,
        load_YAML_parameters,
        load_iSDA_soil_data_alternate,
        run_model,
    )

    assert callable(initialize_simulation)
    assert callable(calc_day_length_raster_fast)
    assert callable(initialize_default_irrigation)
    assert callable(calculate_once_daily_thermal_time)
    assert callable(run_model)
    assert callable(load_YAML_parameters)
    assert callable(load_iSDA_soil_data_alternate)
    assert inspect.signature(run_model).parameters["engine"].default == "xarray"

    notebook_namespace = {}
    exec("from sarra_py import *", notebook_namespace)
    for name in (
        "initialize_simulation",
        "calc_day_length_raster_fast",
        "initialize_default_irrigation",
        "calculate_once_daily_thermal_time",
        "run_model",
        "load_YAML_parameters",
        "load_iSDA_soil_data_alternate",
    ):
        assert callable(notebook_namespace[name])


@pytest.mark.skipif(not DATA_AVAILABLE, reason="Exemple 12 notebook data is not available")
def test_exemple12_reduced_realistic_benchmark_numpy_matches_xarray():
    result = run_realistic_benchmark(
        duration=32,
        subset_y=3,
        subset_x=2,
        scenario_names=("Baseline",),
        check=True,
        rtol=1e-5,
        atol=1e-5,
    )

    assert result["notebook"] == str(NOTEBOOK_PATH.relative_to(NOTEBOOK_PATH.parents[1]))
    assert result["duration"] == 32
    assert result["grid_y"] == 3
    assert result["grid_x"] == 2
    assert set(result["comparison"]["value_variables"]) == set(NOTEBOOK_VALUE_VARIABLES)
    assert set(result["comparison"]["summary_variables"]) == set(SUMMARY_VARIABLES)
    assert result["comparison"]["equal_nan"] is True

    baseline = result["scenarios"]["Baseline"]
    assert baseline["xarray"]["run_seconds"] >= 0
    assert baseline["numpy"]["run_seconds"] >= 0
    assert baseline["speedup_run"] > 0
    assert result["totals"]["speedup_total"] > 0
