"""Regression scenarios for the approved readiness-audit corrections."""
from datetime import date, timedelta

import numpy as np
import pytest
import rasterio
import xarray as xr
from rasterio.transform import from_origin

from model_fixtures import (
    build_input_dataset, sample_itk_params, sample_variety_params,
)
from sarra_py import ModelParameters, SimulationConfig, run_simulation, initialize_simulation
from sarra_py.bilan_hydro import compute_irrigation_state, compute_daily_irrigation
from sarra_py.bilan_pheno import update_root_growth_speed
from sarra_py.data_preparation import load_TAMSAT_data, load_TAMSAT_data_fast

START = date(2020, 5, 1)


def container(values, backend):
    if backend == "numpy":
        return values
    return xr.Dataset({name: (("time", "y", "x"), value)
                       for name, value in values.items()})


@pytest.mark.parametrize("engine", ["numpy", "xarray"])
@pytest.mark.parametrize("model", ["full", "waterbalance"])
@pytest.mark.parametrize("automatic", [False, True])
def test_prescribed_irrigation_applied_independently_of_automatic_mode(engine, model, automatic):
    data = build_input_dataset(duration=4, width=1, height=1)
    for name in ("rain", "ET0", "stockIniSurf", "stockIniProf"):
        data[name][:] = 0.
    doses = np.array([10., 0., 5., 2.], dtype="float32")
    data["irrigation"] = (data.rain.dims, doses[:, None, None])
    original = data.copy(deep=True)
    management = sample_itk_params(START + timedelta(days=10))
    management["irrigAuto"] = automatic
    result = run_simulation(data, ModelParameters(sample_variety_params(), management, {}),
                            SimulationConfig(START, 4, engine=engine, model=model))
    np.testing.assert_allclose(result.irrigTotDay[:, 0, 0], doses)
    np.testing.assert_allclose(result.available_water[:, 0, 0], doses)
    assert float(result.surface_tank_stock[-1, 0, 0]) == pytest.approx(17.)
    assert float(result.total_tank_stock[-1, 0, 0]) == pytest.approx(17.)
    xr.testing.assert_identical(data, original)


@pytest.mark.parametrize("backend", ["numpy", "xarray"])
def test_automatic_irrigation_supplements_prescription_and_respects_phase(backend):
    # First two cells are active, the third is inactive, fourth has no dose.
    values = {name: np.array([[v]], dtype=float) for name, v in {
        "irrigAuto": [1, 1, 1, 1], "numPhase": [2, 2, 0, 2],
        "irrigation_tank_stock": [10, 10, 0, 10],
        "irrigation_tank_capacity": [30, 30, 0, 30],
        "irrigation": [5, 20, 5, 0], "irrigTotDay": [99, 99, 99, 99],
    }.items()}
    data = container(values, backend)
    with np.errstate(divide="raise", invalid="raise"):
        compute_daily_irrigation(0, data, {"irrigAutoTarget": .8, "maxIrrig": 8.})
    np.testing.assert_allclose(np.asarray(data["irrigTotDay"]), [[[13, 20, 5, 8]]])


@pytest.mark.parametrize("backend", ["numpy", "xarray"])
def test_lower_level_rainfed_call_needs_no_irrigation_field(backend):
    data = container({"irrigTotDay": np.ones((1, 1, 1))}, backend)
    compute_irrigation_state(0, data, {"irrigAuto": False})
    np.testing.assert_array_equal(np.asarray(data["irrigTotDay"]), 0.)


@pytest.mark.parametrize("spatial_dims", [("x", "y"), ("y", "x")])
def test_initial_surface_and_deep_stocks_have_consistent_total(spatial_dims):
    data = build_input_dataset(duration=2, width=2, height=2)
    if spatial_dims == ("y", "x"):
        data = data.transpose("time", "y", "x")
    surface = np.array([[0., 10.], [20., 25.]], dtype="float32")
    deep = np.array([[30., 25.], [5., 40.]], dtype="float32")
    data["stockIniSurf"].data = surface
    data["stockIniProf"].data = deep
    result = initialize_simulation(data, 2, 2, 2, sample_variety_params(),
                                   sample_itk_params(START), START)
    for t in range(2):
        np.testing.assert_allclose(result.surface_tank_stock[t], surface)
        np.testing.assert_allclose(result.total_tank_stock[t], surface + deep)
        np.testing.assert_allclose(result.previous_total_tank_stock[t], surface + deep)
    assert result.surface_tank_stock.attrs["units"] == "mm"


@pytest.mark.parametrize("engine", ["numpy", "xarray"])
def test_initial_surface_stock_is_retained_without_fluxes(engine):
    data = build_input_dataset(duration=3, width=1, height=1)
    data["rain"][:] = 0.
    data["ET0"][:] = 0.
    data["stockIniSurf"][:] = 20.
    data["stockIniProf"][:] = 30.
    result = run_simulation(data, ModelParameters(sample_variety_params(),
                            sample_itk_params(START + timedelta(days=10)), {}),
                            SimulationConfig(START, 3, engine=engine))
    np.testing.assert_allclose(result.surface_tank_stock, 20.)
    np.testing.assert_allclose(result.total_tank_stock, 50.)


@pytest.mark.parametrize("backend", ["numpy", "xarray"])
def test_root_speed_uses_each_phase_parameter_including_phase_six(backend):
    data = container({"numPhase": np.arange(8, dtype=float)[None, None, :],
                      "vRac": np.full((1, 1, 8), 25.)}, backend)
    variety = sample_variety_params()
    variety.update(VRacLevee=11., VRacBVP=12., VRacPSP=13., VRacRPR=14.,
                   VRacMatu1=25., VRacMatu2=2.)
    update_root_growth_speed(0, data, variety)
    np.testing.assert_allclose(np.asarray(data["vRac"]), [[[0, 11, 12, 13, 14, 25, 2, 0]]])


@pytest.mark.parametrize("loader", [load_TAMSAT_data, load_TAMSAT_data_fast])
@pytest.mark.parametrize("nodata", [-9999., -32768., np.nan])
def test_rainfall_loaders_mask_declared_nodata_without_filling(tmp_path, loader, nodata):
    values = np.array([[0., 10.], [nodata, np.nan]], dtype="float32")
    for day in (1, 2):
        with rasterio.open(tmp_path / f"rain_2020_05_{day:02d}.tif", "w",
                           driver="GTiff", height=2, width=2, count=1,
                           dtype="float32", crs="EPSG:4326", nodata=nodata,
                           transform=from_origin(0, 2, 1, 1)) as raster:
            raster.write(values, 1)
    result = loader(xr.Dataset(), tmp_path, START, 2)
    try:
        np.testing.assert_allclose(result.rain.values, np.repeat(
            np.array([[[0., 10.], [np.nan, np.nan]]]), 2, axis=0), equal_nan=True)
        np.testing.assert_array_equal(result.time.values,
                                     np.array(["2020-05-01", "2020-05-02"], dtype="datetime64[ns]"))
        assert result.rain.attrs["units"] == "mm"
    finally:
        result.close()
