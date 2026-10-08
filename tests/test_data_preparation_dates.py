import datetime as dt
from pathlib import Path

import numpy as np
import pytest
import rasterio
import rioxarray  # noqa: F401 - registers the rio accessor
import xarray as xr
from rasterio.transform import from_origin

from sarra_py.data_preparation import (
    build_rainfall_files_df,
    get_grid_size,
    load_AgERA5_data,
    load_AgERA5_data_fast_dask,
    load_TAMSAT_data_fast,
)


def _write_raster(path, value):
    with rasterio.open(
        path, "w", driver="GTiff", height=2, width=2, count=1,
        dtype="float32", crs="EPSG:4326", transform=from_origin(0, 2, 1, 1),
    ) as raster:
        raster.write(np.full((2, 2), value, dtype="float32"), 1)


def test_daily_rasters_are_filtered_and_sorted_by_date(tmp_path):
    for day in (3, 1, 2):
        (tmp_path / f"rain_2020_01_{day:02d}.tif").touch()
    (tmp_path / "rain_2020_01_02.tif.aux.xml").touch()
    (tmp_path / "notes.txt").touch()

    files = build_rainfall_files_df(tmp_path, dt.date(2020, 1, 2), 2)
    assert files["filename"].tolist() == ["rain_2020_01_02.tif", "rain_2020_01_03.tif"]


@pytest.mark.parametrize(
    "names, duration, issue",
    [
        (["rain_2020_01_01.tif", "rain_2020_01_03.tif"], 3, "missing dates"),
        (["rain_2020_01_01.tif", "other_2020_01_01.tif", "rain_2020_01_02.tif"], 2, "duplicate dates"),
    ],
)
def test_daily_rasters_reject_missing_or_duplicate_dates(tmp_path, names, duration, issue):
    for name in names:
        (tmp_path / name).touch()
    with pytest.raises(ValueError, match=issue):
        build_rainfall_files_df(tmp_path, dt.date(2020, 1, 1), duration)


def test_grid_size_rejects_missing_middle_day_before_opening_raster(tmp_path):
    (tmp_path / "rain_2020_01_01.tif").touch()
    (tmp_path / "rain_2020_01_03.tif").touch()
    with pytest.raises(ValueError, match="missing dates"):
        get_grid_size(tmp_path, dt.date(2020, 1, 1), 3)


def test_agera5_loader_uses_requested_dates_and_preserves_mapping(tmp_path):
    values = {
        "2m_temperature_24_hour_mean": (10, 20, 30),
        "ET0Hargeaves": (1, 2, 3),
        "solar_radiation_flux_daily": (1000, 2000, 3000),
    }
    for variable, daily_values in values.items():
        folder = tmp_path / variable
        folder.mkdir()
        for day in (3, 1, 2):
            _write_raster(folder / f"{variable}_2020_01_{day:02d}.tif", daily_values[day - 1])

    rain = xr.DataArray(
        np.zeros((2, 2, 2), dtype="float32"), dims=("time", "y", "x"),
        coords={"time": [0, 1], "y": [1.5, 0.5], "x": [0.5, 1.5]},
    )
    rain.rio.write_crs("EPSG:4326", inplace=True)
    data = xr.Dataset({"rain": rain})

    result = load_AgERA5_data(data, tmp_path, dt.date(2020, 1, 2), 2)
    np.testing.assert_allclose(result["tpMoy"][:, 0, 0], [20, 30])
    np.testing.assert_allclose(result["ET0"][:, 0, 0], [2, 3])
    np.testing.assert_allclose(result["rg"][:, 0, 0], [2, 3])


def test_agera5_fast_loader_rejects_incomplete_dates(tmp_path):
    folder = tmp_path / "2m_temperature_24_hour_mean"
    folder.mkdir()
    (folder / "temperature_2020_01_01.tif").touch()
    (folder / "temperature_2020_01_03.tif").touch()
    with pytest.raises(ValueError, match="missing dates"):
        load_AgERA5_data_fast_dask(xr.Dataset(), tmp_path, dt.date(2020, 1, 1), 3)


def test_agera5_fast_loader_receives_only_requested_dates(tmp_path, monkeypatch):
    for variable in ("2m_temperature_24_hour_mean", "ET0Hargeaves",
                     "solar_radiation_flux_daily"):
        folder = tmp_path / variable
        folder.mkdir()
        for day in (3, 1, 2):
            (folder / f"{variable}_2020_01_{day:02d}.tif").touch()

    received_paths = []

    def capture_paths(paths, **kwargs):
        received_paths.extend(paths)
        raise RuntimeError("stop after file selection")

    monkeypatch.setattr(xr, "open_mfdataset", capture_paths)
    with pytest.raises(RuntimeError, match="stop after file selection"):
        load_AgERA5_data_fast_dask(xr.Dataset(), tmp_path, dt.date(2020, 1, 2), 2)

    assert [Path(path).name for path in received_paths] == [
        "2m_temperature_24_hour_mean_2020_01_02.tif",
        "2m_temperature_24_hour_mean_2020_01_03.tif",
    ]


def test_agera5_unused_folder_does_not_require_daily_coverage(tmp_path):
    from sarra_py.data_preparation import _list_agera5_files

    used = tmp_path / "2m_temperature_24_hour_mean"
    used.mkdir()
    (used / "temperature_2020_01_01.tif").touch()
    (tmp_path / "2m_temperature_24_hour_maximum").mkdir()

    variables, files = _list_agera5_files(tmp_path, dt.date(2020, 1, 1), 1)

    assert "2m_temperature_24_hour_maximum" in variables
    assert list(files) == ["2m_temperature_24_hour_mean"]


def test_raw_tamsat_agera5_adapter_keeps_daily_alignment(tmp_path):
    from sarra_py.application import load_tamsat_agera5

    rainfall = tmp_path / "rainfall"
    climate = tmp_path / "climate"
    rainfall.mkdir()
    values = {
        "2m_temperature_24_hour_mean": (25, 26),
        "ET0Hargeaves": (4, 5),
        "solar_radiation_flux_daily": (18000, 19000),
    }
    for day in (2, 1):
        _write_raster(rainfall / f"rain_2020_01_{day:02d}.tif", day * 10)
    for variable, daily_values in values.items():
        folder = climate / variable
        folder.mkdir(parents=True)
        for day in (2, 1):
            _write_raster(folder / f"{variable}_2020_01_{day:02d}.tif", daily_values[day - 1])
    soil = xr.Dataset(
        {"ru": (("y", "x"), np.full((2, 2), 150.0))},
        coords={"y": [1.5, 0.5], "x": [0.5, 1.5]},
    )
    soil_path = tmp_path / "soil.nc"
    soil.to_netcdf(soil_path)

    data = load_tamsat_agera5(rainfall, climate, soil_path, dt.date(2020, 1, 1), 2)

    np.testing.assert_array_equal(
        data["time"].values.astype("datetime64[D]"),
        np.array(["2020-01-01", "2020-01-02"], dtype="datetime64[D]"),
    )
    np.testing.assert_allclose(data["rain"][:, 0, 0], [10, 20])
    np.testing.assert_allclose(data["tpMoy"][:, 0, 0], [25, 26])
    np.testing.assert_allclose(data["rg"][:, 0, 0], [18, 19])



def test_agera5_loader_reports_missing_required_folder(tmp_path):
    (tmp_path / "2m_temperature_24_hour_mean").mkdir()
    (tmp_path / "2m_temperature_24_hour_mean" / "temperature_2020_01_01.tif").touch()
    with pytest.raises(ValueError, match="Missing AgERA5 forcing folders"):
        load_AgERA5_data(xr.Dataset(), tmp_path, dt.date(2020, 1, 1), 1)



def test_fast_tiff_loaders_read_and_align_daily_values(tmp_path):
    rain_dir = tmp_path / "rain"
    climate_dir = tmp_path / "climate"
    rain_dir.mkdir()
    variables = {
        "2m_temperature_24_hour_mean": (25, 26),
        "ET0Hargeaves": (4, 5),
        "solar_radiation_flux_daily": (18000, 19000),
    }
    for variable in variables:
        (climate_dir / variable).mkdir(parents=True)
    for day in (2, 1):
        _write_raster(rain_dir / f"rain_2020_01_{day:02d}.tif", day * 10)
        for variable, values in variables.items():
            _write_raster(
                climate_dir / variable / f"{variable}_2020_01_{day:02d}.tif",
                values[day - 1],
            )

    data = load_TAMSAT_data_fast(xr.Dataset(), rain_dir, dt.date(2020, 1, 1), 2)
    data = load_AgERA5_data_fast_dask(data, climate_dir, dt.date(2020, 1, 1), 2)

    np.testing.assert_array_equal(
        data["time"].values.astype("datetime64[D]"),
        np.array(["2020-01-01", "2020-01-02"], dtype="datetime64[D]"),
    )
    np.testing.assert_allclose(data["rain"][:, 0, 0], [10, 20])
    np.testing.assert_allclose(data["tpMoy"][:, 0, 0], [25, 26])
    np.testing.assert_allclose(data["rg"][:, 0, 0], [18, 19])
