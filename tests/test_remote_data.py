from datetime import date
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pytest
import xarray as xr

from sarra_py import remote_data


def _daily_file(path, variable, value, day, *, descending=False, latitudes=None, longitudes=None):
    lat = latitudes if latitudes is not None else (
        [13.85, 13.75] if descending else [13.75, 13.85]
    )
    lon = longitudes if longitudes is not None else [2.05, 2.15]
    data = xr.Dataset(
        {variable: (("time", "lat", "lon"),
                    np.full((1, len(lat), len(lon)), value, dtype="float32"))},
        coords={"time": [np.datetime64(day, "ns")], "lat": lat,
                "lon": lon},
    )
    data = data.assign_coords(crs=0)
    data[variable].attrs["grid_mapping"] = "crs"
    data.to_netcdf(path)


def test_prepare_remote_inputs_converts_units_and_aligns_grid(tmp_path, monkeypatch):
    rain = tmp_path / "rain.nc"
    temp = tmp_path / "temp.nc"
    et0 = tmp_path / "et0.nc"
    radiation = tmp_path / "radiation.nc"
    _daily_file(
        rain, "rfe_filled", 5.0, "2017-04-01",
        latitudes=[13.8875, 13.85, 13.8125, 13.775, 13.7375],
        longitudes=[2.0125, 2.05, 2.0875, 2.125, 2.1625],
    )
    _daily_file(temp, "Temperature_Air_2m_Mean_24h", 300.0,
                "2017-04-01", descending=True)
    _daily_file(et0, "ReferenceET_PenmanMonteith_FAO56", 4.0,
                "2017-04-01", descending=True)
    _daily_file(radiation, "Solar_Radiation_Flux", 20_000_000.0,
                "2017-04-01", descending=True)

    def fake_soil(data, rows, columns, assets_dir=None):
        for name in ("ru", "epaisseurSurf", "epaisseurProf", "profRu",
                     "stockIniProf", "stockIniSurf", "runoff_threshold",
                     "runoff_rate"):
            data[name] = (("y", "x"), np.ones((rows, columns), dtype="float32"))
        return data

    monkeypatch.setattr(remote_data, "load_iSDA_soil_data", fake_soil)
    prepared = remote_data.prepare_remote_inputs(
        [rain], {"tpMoy": [temp], "ET0": [et0], "rg": [radiation]},
        (13.9, 2.0, 13.7, 2.2), tmp_path, date(2017, 4, 1), 1,
    )
    assert prepared.rain.dims == ("time", "y", "x")
    assert prepared.sizes["y"] == prepared.sizes["x"] == 5
    np.testing.assert_allclose(prepared.x, [2.0125, 2.05, 2.0875, 2.125, 2.1625])
    np.testing.assert_allclose(prepared.y, [13.8875, 13.85, 13.8125, 13.775, 13.7375])
    np.testing.assert_allclose(prepared.rain.values, 5)
    np.testing.assert_allclose(prepared.tpMoy.values, 26.85, atol=0.01)
    np.testing.assert_allclose(prepared.ET0.values, 4)
    np.testing.assert_allclose(prepared.rg.values, 20)
    assert prepared.ET0.attrs["source"] == "AgERA5 v2 Penman-Monteith FAO56"


def test_prepare_remote_inputs_rejects_climate_edge_gaps(tmp_path):
    rain = tmp_path / "rain.nc"
    climate = tmp_path / "climate.nc"
    _daily_file(
        rain, "rfe_filled", 5.0, "2017-04-01",
        latitudes=[13.8875, 13.85, 13.8125, 13.775, 13.7375],
        longitudes=[2.0125, 2.05, 2.0875, 2.125, 2.1625],
    )
    _daily_file(
        climate, "Temperature_Air_2m_Mean_24h", 300.0, "2017-04-01",
        latitudes=[13.8, 13.7], longitudes=[2.1, 2.2],
    )
    with pytest.raises(ValueError, match="tpMoy has .* missing values"):
        remote_data.prepare_remote_inputs(
            [rain], {"tpMoy": [climate], "ET0": [climate], "rg": [climate]},
            (13.9, 2.0, 13.7, 2.2), tmp_path, date(2017, 4, 1), 1,
        )


def test_tamsat_download_caches_valid_netcdf(tmp_path, monkeypatch):
    source = tmp_path / "source.nc"
    _daily_file(source, "rfe_filled", 3, "2017-04-01")
    urls = []

    class Response(BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_):
            self.close()

    def fake_urlopen(url, timeout):
        urls.append(url)
        return Response(source.read_bytes())

    monkeypatch.setattr(remote_data, "urlopen", fake_urlopen)
    cache = tmp_path / "cache"
    first = remote_data.download_tamsat_daily(date(2017, 4, 1), 1,
                                               cache, progress=False)
    second = remote_data.download_tamsat_daily(date(2017, 4, 1), 1,
                                                cache, progress=False)
    assert first == second
    assert len(urls) == 1
    assert urls[0].endswith("/2017/04/rfe2017_04_01.v3.1.nc")


def test_agera5_monthly_requests_and_cache(tmp_path):
    calls = []

    class Client:
        def retrieve(self, dataset, request, target):
            calls.append((dataset, request))
            with ZipFile(target, "w") as archive:
                inner = tmp_path / "daily.nc"
                _daily_file(inner, request["variable"], 1, "2017-04-01")
                archive.write(inner, "nested/daily.nc")

    cache = tmp_path / "cache"
    first = remote_data.download_agera5_v2(
        date(2017, 4, 1), 1, (13.9, 2.0, 13.7, 2.2), cache,
        client=Client(), progress=False)
    second = remote_data.download_agera5_v2(
        date(2017, 4, 1), 1, (13.9, 2.0, 13.7, 2.2), cache,
        client=Client(), progress=False)
    assert first == second
    assert len(calls) == 3
    assert all(call[0] == remote_data.AGERA5_DATASET for call in calls)
    assert all(call[1]["area"] == [14.1, 1.8, 13.5, 2.4] for call in calls)
    assert all(call[1]["version"] == "2_0" for call in calls)
    assert all(len(paths) == 1 for paths in first.values())
