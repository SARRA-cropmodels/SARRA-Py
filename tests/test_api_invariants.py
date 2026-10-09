import datetime as dt

import numpy as np
import xarray as xr

import sarra_py
from benchmarks.benchmark_run_model import (
    build_input_dataset,
    sample_itk_params,
    sample_variety_params,
)
from sarra_py import (
    calc_day_length_raster_fast,
    initialize_simulation,
    run_model,
    run_waterbalance_model,
)
from sarra_py.bilan_carbo import variable_dict
from sarra_py.data_preparation import _cached_day_length_matrix


def test_public_model_defaults_use_numpy_engine():
    assert sarra_py.SimulationConfig(dt.date(2020, 1, 1), 1).engine == "numpy"
    assert run_model.__defaults__[-2:] == ("numpy", True)
    assert run_waterbalance_model.__defaults__[-2:] == ("numpy", True)


def test_key_notebook_functions_remain_importable_from_package_root():
    expected_names = [
        "build_rainfall_files_df",
        "get_grid_size",
        "load_TAMSAT_data",
        "load_AgERA5_data",
        "load_iSDA_soil_data",
        "load_iSDA_soil_data_alternate",
        "load_YAML_parameters",
        "calc_day_length_raster_fast",
        "initialize_default_irrigation",
        "initialize_simulation",
        "calculate_once_daily_thermal_time",
        "calculate_daily_thermal_time",
        "run_model",
        "run_waterbalance_model",
    ]

    for name in expected_names:
        assert callable(getattr(sarra_py, name))


def test_initialize_simulation_preserves_tiny_dataset_invariants():
    duration = 8
    width = 3
    height = 2
    date_start = dt.date(2020, 5, 1)
    data = build_input_dataset(
        duration=duration,
        width=width,
        height=height,
        seed=2026,
    )
    original_sizes = dict(data.sizes)
    original_attrs = dict(data.attrs)
    original_coords = {
        name: coord.values.copy()
        for name, coord in data.coords.items()
    }
    original_data_vars = set(data.data_vars)
    original_var_attrs = {
        name: dict(data[name].attrs)
        for name in data.data_vars
    }

    initialized = initialize_simulation(
        data.copy(deep=True),
        width,
        height,
        duration,
        sample_variety_params(),
        sample_itk_params(date_start),
        date_start,
    )

    assert isinstance(initialized, xr.Dataset)
    assert dict(initialized.sizes) == original_sizes
    assert initialized.attrs == original_attrs
    assert original_data_vars.issubset(set(initialized.data_vars))

    for coord_name, coord_values in original_coords.items():
        assert coord_name in initialized.coords
        np.testing.assert_array_equal(
            initialized.coords[coord_name].values,
            coord_values,
        )

    for name, attrs in original_var_attrs.items():
        assert initialized[name].attrs == attrs

    rain_dims = data["rain"].dims
    rain_shape = data["rain"].shape
    expected_daily_vars = {
        "sowing_date",
        "irrigAuto",
        "biomMc",
        "ltr",
        "LitTige",
        "root_tank_capacity",
        "total_tank_stock",
        "humectation_front",
        "previous_humectation_front",
        "previous_total_tank_stock",
        "par",
        "rapDensite",
        *variable_dict().keys(),
    }
    expected_static_vars = {"surface_tank_capacity"}

    assert expected_daily_vars.issubset(set(initialized.data_vars))
    assert expected_static_vars.issubset(set(initialized.data_vars))

    for name in expected_daily_vars:
        assert initialized[name].dims == rain_dims
        assert initialized[name].shape == rain_shape
        for coord_name in rain_dims:
            np.testing.assert_array_equal(
                initialized[name].coords[coord_name].values,
                initialized["rain"].coords[coord_name].values,
            )

    for name in expected_static_vars:
        assert initialized[name].dims == data["ru"].dims
        assert initialized[name].shape == data["ru"].shape
        for coord_name in data["ru"].dims:
            np.testing.assert_array_equal(
                initialized[name].coords[coord_name].values,
                initialized["ru"].coords[coord_name].values,
            )

    expected_attrs = {
        "irrigAuto": {
            "units": "binary",
            "long_name": "automatic irrigation indicator",
        },
        "biomMc": {
            "units": "kg/ha",
            "long_name": "Initial biomass of crop residues (mulch)",
        },
        "LitTige": {
            "units": "kg/ha",
            "long_name": "Initial biomass of stem residues as litter",
        },
        "root_tank_capacity": {
            "units": "mm",
            "long_name": "Soil maximum water storage capacity",
        },
        "surface_tank_capacity": {
            "units": "mm",
            "long_name": "Maximum water capacity of surface tank",
        },
        "total_tank_stock": {"units": "mm", "long_name": "?"},
        "humectation_front": {
            "units": "mm",
            "long_name": "Maximum water capacity to humectation front",
        },
        "par": {"units": "MJ/m2", "long_name": "par"},
        "rapDensite": {
            "units": "none",
            "long_name": "sowing density adjustement factor",
        },
    }
    for name, attrs in expected_attrs.items():
        assert initialized[name].attrs == attrs

    for name, (long_name, units) in variable_dict().items():
        assert initialized[name].attrs == {
            "units": units,
            "long_name": long_name,
        }


def test_calc_day_length_raster_fast_is_stable_for_identical_calls():
    duration = 8
    data = build_input_dataset(duration=duration, width=3, height=2, seed=2026)
    date_start = dt.date(2020, 5, 1)
    _cached_day_length_matrix.cache_clear()

    first = calc_day_length_raster_fast(data.copy(deep=True), date_start, duration)
    first_cache_info = _cached_day_length_matrix.cache_info()
    second = calc_day_length_raster_fast(data.copy(deep=True), date_start, duration)
    second_cache_info = _cached_day_length_matrix.cache_info()

    assert first["dureeDuJour"].dims == data["rain"].dims
    assert second["dureeDuJour"].dims == first["dureeDuJour"].dims
    assert second_cache_info.hits == first_cache_info.hits + 1

    for coord_name in first["dureeDuJour"].coords:
        assert coord_name in second["dureeDuJour"].coords
        np.testing.assert_array_equal(
            first["dureeDuJour"].coords[coord_name].values,
            second["dureeDuJour"].coords[coord_name].values,
        )

    np.testing.assert_allclose(
        first["dureeDuJour"].values,
        second["dureeDuJour"].values,
        rtol=0,
        atol=0,
        equal_nan=True,
    )
