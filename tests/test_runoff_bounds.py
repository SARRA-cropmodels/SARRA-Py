from datetime import date

import numpy as np
import pytest
import xarray as xr

from model_fixtures import (
    build_input_dataset,
    sample_itk_params,
    sample_variety_params,
)
from sarra_py import ModelParameters, SimulationConfig, run_simulation
from sarra_py.bilan_hydro import compute_runoff


@pytest.mark.parametrize("container", ["numpy", "xarray"])
def test_runoff_is_nonnegative_and_cannot_exceed_available_water(container):
    values = {
        "rain": np.array([[[30., 30., 30., 10., 20., 30., 30.]]]),
        "available_water": np.array([[[1.5, 30., 30., 30., 100., 0., np.nan]]]),
        "runoff_threshold": np.full((1, 7), 20.),
        "runoff_rate": np.array([[.27, .27, 4., .27, .27, .27, .27]]),
        "runoff": np.zeros((1, 1, 7)),
    }
    if container == "xarray":
        data = xr.Dataset({
            name: (("time", "y", "x") if value.ndim == 3 else ("y", "x"), value)
            for name, value in values.items()
        })
    else:
        data = values

    compute_runoff(0, data)

    np.testing.assert_allclose(
        np.asarray(data["runoff"])[0, 0],
        [0., 2.7, 30., 0., 0., 0., np.nan],
        equal_nan=True,
    )
    np.testing.assert_allclose(
        np.asarray(data["available_water"])[0, 0],
        [1.5, 27.3, 0., 30., 100., 0., np.nan],
        equal_nan=True,
    )


@pytest.mark.parametrize("engine", ["numpy", "xarray"])
def test_mulch_interception_does_not_create_water_through_negative_runoff(engine):
    start = date(2020, 5, 1)
    data = build_input_dataset(duration=1, width=1, height=1)
    data["rain"][:] = 30.
    data["ET0"][:] = 0.
    data["runoff_threshold"][:] = 20.
    data["runoff_rate"][:] = .27
    management = sample_itk_params(start)
    management.update(biomIniMc=3000., humSatMc=100., surfMc=1.)

    result = run_simulation(
        data, ModelParameters(sample_variety_params(), management, {}),
        SimulationConfig(start, 1, engine=engine),
    )

    assert float(result["runoff"][0, 0, 0]) == 0.
    np.testing.assert_allclose(
        result["water_captured_by_mulch"] + result["runoff"] + result["available_water"],
        result["rain"], rtol=1e-6, atol=1e-6,
    )
