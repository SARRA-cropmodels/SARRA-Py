import datetime as dt
from pathlib import Path

import numpy as np
import pytest
import rasterio
import xarray as xr
import yaml
from rasterio.transform import from_origin

from benchmarks.benchmark_run_model import (
    assert_equivalent_outputs,
    build_input_dataset,
    sample_itk_params,
    sample_variety_params,
)
from sarra_py import (
    ModelParameters,
    SimulationConfig,
    load_model_parameters,
    calculate_once_daily_thermal_time,
    initialize_default_irrigation,
    initialize_simulation,
    load_iSDA_soil_data_alternate,
    run_model,
    run_simulation,
    select_daily_window,
)
from sarra_py.cli import main


def _parameters(start):
    return ModelParameters(sample_variety_params(), sample_itk_params(start), {})


def test_high_level_api_matches_existing_notebook_sequence():
    start = dt.date(2020, 5, 1)
    base = build_input_dataset(duration=8, width=3, height=2)
    parameters = _parameters(start)
    manual = initialize_simulation(
        base.copy(deep=True), 3, 2, 8,
        parameters.variety.copy(), parameters.management.copy(), start,
    )
    manual = initialize_default_irrigation(manual)
    manual = calculate_once_daily_thermal_time(manual, parameters.variety)
    manual = run_model(
        parameters.variety.copy(), parameters.management.copy(), {},
        manual, 8, progress=False,
    )

    result = run_simulation(base, parameters, SimulationConfig(start, 8))

    assert_equivalent_outputs(manual, result)
    assert "rdt" not in base
    assert "rapDensite" not in parameters.management


def test_high_level_api_rejects_missing_parameters_and_misaligned_time():
    start = dt.date(2020, 5, 1)
    base = build_input_dataset(duration=3, width=2, height=2)
    wrong = base.assign_coords(time=np.array(["2020-05-01", "2020-05-03", "2020-05-04"], dtype="datetime64[ns]"))
    with pytest.raises(ValueError, match="time coordinates"):
        run_simulation(wrong, _parameters(start), SimulationConfig(start, 3))

    variety = sample_variety_params()
    del variety["TBase"]
    with pytest.raises(ValueError, match="TBase"):
        run_simulation(base, ModelParameters(variety, sample_itk_params(start), {}), SimulationConfig(start, 3))


def test_cli_runs_prepared_netcdf_with_relative_paths(tmp_path, capsys):
    start = dt.date(2020, 5, 1)
    data = build_input_dataset(duration=8, width=3, height=2)
    data.to_netcdf(tmp_path / "input.nc")
    variety = sample_variety_params()
    management = sample_itk_params(start)
    management["DateSemis"] = start.isoformat()
    for name, values in (("variety", variety), ("management", management), ("soil", {})):
        (tmp_path / f"{name}.yaml").write_text(yaml.safe_dump(values), encoding="utf-8")
    config = {
        "input": {"kind": "prepared_netcdf", "path": "input.nc"},
        "parameters": {
            "variety": "variety.yaml", "management": "management.yaml", "soil": "soil.yaml",
        },
        "simulation": {"date_start": start.isoformat(), "duration": 8, "progress": False},
        "output": {"path": "outputs/result.nc"},
    }
    config_path = tmp_path / "run.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    assert main([str(config_path)]) == 0
    assert str(tmp_path / "outputs" / "result.nc") in capsys.readouterr().out
    with xr.open_dataset(tmp_path / "outputs" / "result.nc") as result:
        assert result.sizes["time"] == 8
        assert "rdt" in result

    with pytest.raises(SystemExit) as exc:
        main([str(config_path)])
    assert exc.value.code == 2



def test_reference_parameter_files_load_outside_repo_cwd(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(tmp_path)
    parameters = load_model_parameters(
        root / "data/params/variety/millet_variety.yaml",
        root / "data/params/itk/millet_niger_2017.yaml",
        root / "data/params/soil/USA_iowa_V42.yaml",
    )
    assert parameters.management["DateSemis"] == dt.date(2016, 5, 1)
    assert "TBase" in parameters.variety


def test_api_rejects_nonconsecutive_positional_time_and_nonboolean_progress():
    start = dt.date(2020, 5, 1)
    base = build_input_dataset(duration=3, width=2, height=2)
    wrong = base.assign_coords(time=[0, 2, 3])
    with pytest.raises(ValueError, match="consecutive indices"):
        run_simulation(wrong, _parameters(start), SimulationConfig(start, 3))
    with pytest.raises(ValueError, match="progress must be boolean"):
        SimulationConfig(start, 3, progress="false").validate()
    nonnumeric = base.assign(rain=base["rain"].astype(str))
    with pytest.raises(ValueError, match="rain must contain real numeric values"):
        run_simulation(nonnumeric, _parameters(start), SimulationConfig(start, 3))


def test_cli_runs_tiff_weather_and_gridded_soil(tmp_path, capsys):
    start = dt.date(2020, 1, 1)
    rainfall = tmp_path / "rainfall"
    climate = tmp_path / "climate"
    rainfall.mkdir()
    variables = {
        "2m_temperature_24_hour_mean": 28.0,
        "ET0Hargeaves": 4.0,
        "solar_radiation_flux_daily": 18000.0,
    }
    for variable in variables:
        (climate / variable).mkdir(parents=True)

    def write_raster(path, value):
        with rasterio.open(
            path, "w", driver="GTiff", height=2, width=2, count=1,
            dtype="float32", crs="EPSG:4326", transform=from_origin(0, 2, 1, 1),
        ) as raster:
            raster.write(np.full((2, 2), value, dtype="float32"), 1)

    for day in range(1, 9):
        write_raster(rainfall / f"rain_2020_01_{day:02d}.tif", 10.0)
        for variable, value in variables.items():
            write_raster(
                climate / variable / f"{variable}_2020_01_{day:02d}.tif", value,
            )

    soil_names = ("ru", "epaisseurSurf", "epaisseurProf", "profRu", "stockIniProf",
                  "stockIniSurf", "runoff_threshold", "runoff_rate")
    soil = build_input_dataset(duration=8, width=2, height=2)[list(soil_names)]
    soil = soil.transpose("y", "x").assign_coords(y=[1.5, 0.5], x=[0.5, 1.5])
    soil.to_netcdf(tmp_path / "soil.nc")
    management = sample_itk_params(start)
    management["DateSemis"] = start.isoformat()
    for name, values in (
        ("variety", sample_variety_params()),
        ("management", management),
        ("soil_params", {}),
    ):
        (tmp_path / f"{name}.yaml").write_text(
            yaml.safe_dump(values), encoding="utf-8",
        )
    config = {
        "input": {
            "kind": "tamsat_agera5",
            "rainfall_dir": "rainfall",
            "climate_dir": "climate",
            "soil_dataset": "soil.nc",
        },
        "parameters": {
            "variety": "variety.yaml",
            "management": "management.yaml",
            "soil": "soil_params.yaml",
        },
        "simulation": {"date_start": start.isoformat(), "duration": 8},
        "output": {"path": "result.nc"},
    }
    config_path = tmp_path / "run.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    assert main([str(config_path)]) == 0
    assert capsys.readouterr().out.strip() == str(tmp_path / "result.nc")
    with xr.open_dataset(tmp_path / "result.nc") as result:
        assert result.sizes["time"] == 8
        np.testing.assert_allclose(result["rain"][:, 0, 0], 10.0)
        np.testing.assert_allclose(result["rg"][:, 0, 0], 18.0)
        assert "rdt" in result



def test_select_daily_window_converts_compatible_cf_calendar():
    import cftime

    dates = xr.cftime_range("2001-01-01", periods=5, calendar="noleap")
    values = xr.DataArray(np.arange(5), dims=("time",), coords={"time": dates})
    selected = select_daily_window(values, dt.date(2001, 1, 2), 3)
    np.testing.assert_array_equal(
        selected.time.values.astype("datetime64[D]"),
        np.array(["2001-01-02", "2001-01-03", "2001-01-04"], dtype="datetime64[D]"),
    )

    leap_dates = xr.cftime_range("2000-02-27", periods=4, calendar="noleap")
    leap_data = xr.DataArray(np.arange(4), dims=("time",), coords={"time": leap_dates})
    with pytest.raises(ValueError, match="every Gregorian day"):
        select_daily_window(leap_data, dt.date(2000, 2, 27), 4)

def test_notebook_scenarios_accept_in_memory_weather_and_parameter_variants():
    start = dt.date(2023, 4, 1)
    base = build_input_dataset(duration=8, width=2, height=2)
    baseline_parameters = _parameters(start)
    baseline = run_simulation(base, baseline_parameters, SimulationConfig(start, 8))

    drier = base.copy(deep=True)
    drier["rain"] = drier["rain"] * 0.8
    changed_variety = dict(baseline_parameters.variety)
    changed_variety["TBase"] += 2.0
    variant_parameters = ModelParameters(
        changed_variety, dict(baseline_parameters.management), baseline_parameters.soil,
    )
    variant = run_simulation(drier, variant_parameters, SimulationConfig(start, 8))

    np.testing.assert_allclose(variant["rain"], baseline["rain"] * 0.8)
    assert not np.allclose(variant["ddj"], baseline["ddj"])
    np.testing.assert_allclose(base["rain"], baseline["rain"])
    assert baseline_parameters.variety["TBase"] != changed_variety["TBase"]
    assert "rdt" not in base

def test_alternate_soil_loader_supplies_full_notebook_input_contract(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(root / "notebooks")
    grid = xr.Dataset(coords={"y": [9.57, 9.35], "x": [13.31, 13.53]})
    grid = grid.rio.write_crs("EPSG:4326")
    soil = load_iSDA_soil_data_alternate(grid, 2, 2)

    required = {
        "ru", "epaisseurSurf", "epaisseurProf", "profRu",
        "stockIniProf", "stockIniSurf", "runoff_threshold", "runoff_rate",
    }
    assert required <= set(soil.data_vars)
    assert all(soil[name].dims == ("y", "x") for name in required)
    assert bool(np.isfinite(soil["epaisseurProf"]).any())
