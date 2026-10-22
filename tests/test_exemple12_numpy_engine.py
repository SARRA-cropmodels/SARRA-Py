import inspect

import pytest

from exemple12_inputs import EXEMPLE12_DATA, NOTEBOOK_PATH, load_exemple12_base_data, load_exemple12_parameters
from model_fixtures import assert_equivalent_outputs
from sarra_py import ModelParameters, SimulationConfig, run_simulation
import pandas as pd



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
    assert inspect.signature(run_model).parameters["engine"].default == "numpy"

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


@pytest.mark.skipif(not DATA_AVAILABLE, reason="Example 12 input data is not available")
def test_exemple12_reduced_inputs_numpy_matches_xarray():
    data, _, _, rows, columns = load_exemple12_base_data(duration=32, subset_y=3, subset_x=2)
    variety, management, soil = load_exemple12_parameters()
    start = pd.Timestamp(data.time.values[0]).date()
    parameters = ModelParameters(variety, management, soil)
    reference = run_simulation(data, parameters, SimulationConfig(start, 32, engine="xarray"))
    candidate = run_simulation(data, parameters, SimulationConfig(start, 32, engine="numpy"))
    assert (rows, columns) == (3, 2)
    assert_equivalent_outputs(reference, candidate, rtol=1e-5, atol=1e-5)
