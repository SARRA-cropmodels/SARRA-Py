"""Optional real input preparation for the Example 12 engine regression."""
import copy
import os
from pathlib import Path
from contextlib import contextmanager
import xarray as xr
import rioxarray  # noqa: F401
from sarra_py import load_YAML_parameters, load_iSDA_soil_data_alternate

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebooks" / "SARRA-Py - Exemple 12 - North Cameroon exploration of climate variants.ipynb"
EXEMPLE12_DATA = ROOT / "data" / "exemple_data" / "exemple_12"


@contextmanager
def _working_directory(path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _first_files(directory, pattern, duration):
    files = sorted(Path(directory).glob(pattern))
    if duration is None:
        return files
    if duration > len(files):
        raise ValueError(f"requested duration={duration}, but only {len(files)} files match {directory}/{pattern}")
    return files[:duration]


def _open_weather_variable(files, variable_name, base_data, transform):
    arrays = []
    for path in files:
        with xr.open_dataset(path, engine="netcdf4") as dataset:
            arrays.append(dataset[variable_name].transpose("time", "lat", "lon").load())

    if len(arrays) == 1:
        data = arrays[0]
    else:
        data = xr.concat(arrays, dim="time")

    data = transform(data)
    data = data.rename({"lat": "y", "lon": "x"})
    data = data.rio.write_crs("EPSG:4326")
    data = data.rio.set_spatial_dims(x_dim="x", y_dim="y")
    return data.rio.reproject_match(base_data)


def load_exemple12_parameters():
    with _working_directory(ROOT / "notebooks"):
        param_variety, param_itk, param_soil = load_YAML_parameters(
            "variety_exemple_2.yaml",
            "itk_exemple_2.yaml",
            "USA_iowa_V42.yaml",
        )

    param_variety = copy.deepcopy(param_variety)
    param_itk = copy.deepcopy(param_itk)
    param_soil = copy.deepcopy(param_soil)

    param_variety["SDJRPR"] = 489.0
    param_variety["SDJLevee"] = 250.0
    param_variety["SDJBVP"] = 636.0
    param_variety["slaMin"] = 285.0
    param_variety["slaMax"] = 363.2
    param_variety["SDJMatu1"] = 848.0
    param_variety["SDJMatu2"] = 334.0
    param_variety["KRdtPotA"] = 0.9

    return param_variety, param_itk, param_soil


def load_exemple12_base_data(
    duration=365,
    subset_y=None,
    subset_x=None,
    subset_y_start=0,
    subset_x_start=0,
    load_inputs=True,
):
    rainfall_path = (
        EXEMPLE12_DATA
        / "rainfall"
        / "01-tamsatDaily.v3.1-20230101-20231231-20260318_11.43_16.36_6.8_13.19.nc"
    )
    rainfall_data = xr.open_dataset(rainfall_path)
    rainfall_data = rainfall_data["rfe_filled"].transpose("time", "lat", "lon")
    rainfall_data = rainfall_data.isel(time=slice(0, duration))

    base_data = xr.Dataset()
    base_data["rain"] = rainfall_data
    base_data["rain"].attrs = {"units": "mm", "long_name": "rainfall"}
    base_data = base_data.rename({"lat": "y", "lon": "x"})
    base_data = base_data.rio.set_spatial_dims(x_dim="x", y_dim="y")
    base_data = base_data.rio.write_crs("EPSG:4326")

    if subset_y is not None:
        base_data = base_data.isel(y=slice(subset_y_start, subset_y_start + subset_y))
    if subset_x is not None:
        base_data = base_data.isel(x=slice(subset_x_start, subset_x_start + subset_x))

    tmax_files = _first_files(EXEMPLE12_DATA / "tmax", "*.nc", duration)
    tmin_files = _first_files(EXEMPLE12_DATA / "tmin", "*.nc", duration)
    rg_files = _first_files(EXEMPLE12_DATA / "solar_radiation_flux", "*.nc", duration)

    tmax_data = _open_weather_variable(
        tmax_files,
        "Temperature_Air_2m_Max_24h",
        base_data,
        lambda values: values - 273.15,
    )
    tmin_data = _open_weather_variable(
        tmin_files,
        "Temperature_Air_2m_Min_24h",
        base_data,
        lambda values: values - 273.15,
    )
    tmean_data = (tmax_data + tmin_data) / 2
    base_data["tpMoy"] = tmean_data

    solar_radiation_flux_data = _open_weather_variable(
        rg_files,
        "Solar_Radiation_Flux",
        base_data,
        lambda values: values / 1_000_000,
    )
    base_data["rg"] = solar_radiation_flux_data
    base_data["ET0"] = 0.0023 * (tmax_data - tmin_data) ** 0.5 * tmean_data * base_data["rg"]

    grid_y = len(base_data["y"])
    grid_x = len(base_data["x"])
    with _working_directory(ROOT / "notebooks"):
        base_data = load_iSDA_soil_data_alternate(base_data, grid_y, grid_x)

    if load_inputs:
        base_data = base_data.load()
        tmax_data = tmax_data.load()
        tmin_data = tmin_data.load()

    return base_data, tmax_data, tmin_data, grid_y, grid_x
