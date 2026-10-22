"""Download and prepare official daily TAMSAT and AgERA5 v2 forcing."""

from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile, is_zipfile
import shutil

import numpy as np
from rasterio.enums import Resampling
import rioxarray  # noqa: F401 - registers xarray's rio accessor
import xarray as xr
from tqdm.auto import tqdm

from .api import SimulationConfig, select_daily_window, validate_input_dataset
from .data_preparation import _describe_input_variables, load_iSDA_soil_data

TAMSAT_BASE = "https://gws-access.jasmin.ac.uk/public/tamsat/rfe/data/v3.1/daily"
AGERA5_DATASET = "sis-agrometeorological-indicators"
AGERA5_GRID_PADDING_DEGREES = 0.2
AGERA5_VARIABLES = {
    "tpMoy": ("2m_temperature", "24_hour_mean"),
    "ET0": ("reference_evapotranspiration", None),
    "rg": ("solar_radiation_flux", None),
}


def _dates(date_start, duration):
    if isinstance(date_start, datetime) or not isinstance(date_start, date):
        raise ValueError("date_start must be a date")
    if not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0:
        raise ValueError("duration must be a positive integer")
    return [date_start + timedelta(days=day) for day in range(duration)]


def _bounds(bounds):
    if len(bounds) != 4:
        raise ValueError("bounds must be (north, west, south, east)")
    north, west, south, east = map(float, bounds)
    if not (-90 <= south < north <= 90 and -180 <= west < east <= 180):
        raise ValueError("Invalid geographic bounds")
    return north, west, south, east


def _agera5_bounds(bounds):
    """Add two AgERA5 grid cells so edge rainfall cells have climate coverage."""
    north, west, south, east = _bounds(bounds)
    pad = AGERA5_GRID_PADDING_DEGREES
    return (round(min(90, north + pad), 4), round(max(-180, west - pad), 4),
            round(max(-90, south - pad), 4), round(min(180, east + pad), 4))


def download_tamsat_daily(date_start, duration, cache_dir, *, progress=True):
    """Cache official TAMSAT v3.1 daily NetCDF rainfall files."""
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    files = []
    for day in tqdm(_dates(date_start, duration), desc="TAMSAT rainfall",
                    unit="day", disable=not progress):
        name = f"rfe{day:%Y_%m_%d}.v3.1.nc"
        target = cache / name
        if not target.is_file() or target.stat().st_size == 0:
            url = f"{TAMSAT_BASE}/{day:%Y}/{day:%m}/{name}"
            partial = target.with_suffix(".nc.part")
            try:
                with urlopen(url, timeout=60) as response, partial.open("wb") as output:
                    shutil.copyfileobj(response, output)
                with xr.open_dataset(partial) as dataset:
                    if "rfe_filled" not in dataset:
                        raise ValueError(f"{url} has no rfe_filled rainfall field")
                partial.replace(target)
            finally:
                partial.unlink(missing_ok=True)
        files.append(target)
    return files


def download_agera5_v2(date_start, duration, bounds, cache_dir, *,
                       client=None, progress=True):
    """Cache monthly AgERA5 v2 files with a two-cell spatial buffer."""
    dates = _dates(date_start, duration)
    north, west, south, east = _agera5_bounds(bounds)
    cache = Path(cache_dir)
    # Include the requested box in the cache key to prevent spatial mix-ups.
    box_key = "_".join(f"{value:.4f}" for value in (north, west, south, east))
    months = sorted({(day.year, day.month) for day in dates})
    result = {name: [] for name in AGERA5_VARIABLES}
    jobs = [(name, year, month) for name in AGERA5_VARIABLES
            for year, month in months]
    for name, year, month in tqdm(jobs, desc="AgERA5 climate",
                                  unit="month", disable=not progress):
        variable, statistic = AGERA5_VARIABLES[name]
        days = [day for day in dates if (day.year, day.month) == (year, month)]
        folder = cache / box_key / name / f"{year:04d}_{month:02d}_{days[0].day:02d}_{days[-1].day:02d}"
        marker = folder / ".complete"
        files = sorted(folder.rglob("*.nc")) if marker.exists() else []
        if not files:
            folder.mkdir(parents=True, exist_ok=True)
            for stale in folder.glob("*.nc"):
                stale.unlink()
            archive = folder / "download.part"
            request = {
                "version": "2_0",
                "variable": variable,
                "year": [f"{year:04d}"],
                "month": [f"{month:02d}"],
                "day": [f"{day.day:02d}" for day in days],
                "area": [north, west, south, east],
            }
            if statistic is not None:
                request["statistic"] = [statistic]
            try:
                if client is None:
                    try:
                        import cdsapi
                    except ImportError as exc:
                        raise ImportError("Install cdsapi to download AgERA5 v2") from exc
                    client = cdsapi.Client(quiet=True, progress=False)
                client.retrieve(AGERA5_DATASET, request, str(archive))
                if is_zipfile(archive):
                    with ZipFile(archive) as zipped:
                        members = [item for item in zipped.infolist()
                                   if item.filename.lower().endswith(".nc")]
                        if not members:
                            raise ValueError("CDS archive contains no NetCDF files")
                        for index, member in enumerate(members):
                            # Use generated names: remote archive paths are not trusted.
                            with zipped.open(member) as source, (folder / f"{index:04d}.nc").open("wb") as output:
                                shutil.copyfileobj(source, output)
                else:
                    shutil.copyfile(archive, folder / "0000.nc")
                files = sorted(folder.glob("*.nc"))
                for path in files:
                    with xr.open_dataset(path):
                        pass
                marker.touch()
            finally:
                archive.unlink(missing_ok=True)
        result[name].extend(files)
    return result


def _standardize_grid(field):
    rename = {}
    for original, standard in (("longitude", "x"), ("lon", "x"),
                               ("latitude", "y"), ("lat", "y"),
                               ("valid_time", "time")):
        if original in field.dims and standard not in field.dims:
            rename[original] = standard
    field = field.rename(rename)
    if not {"x", "y"}.issubset(field.dims):
        raise ValueError(f"Expected latitude/longitude dimensions, got {field.dims}")
    for dimension in list(field.dims):
        if dimension not in ("time", "y", "x"):
            if field.sizes[dimension] != 1:
                raise ValueError(f"Unexpected non-singleton dimension: {dimension}")
            field = field.isel({dimension: 0}, drop=True)
    return field.rio.set_spatial_dims(x_dim="x", y_dim="y").rio.write_crs("EPSG:4326")


def _crop(field, bounds):
    north, west, south, east = _bounds(bounds)
    # Coordinate slicing avoids loading global TAMSAT grids into memory.
    x = field.x
    y = field.y
    field = field.sel(x=slice(west, east) if x[0] < x[-1] else slice(east, west))
    field = field.sel(y=slice(south, north) if y[0] < y[-1] else slice(north, south))
    if field.sizes["x"] == 0 or field.sizes["y"] == 0:
        raise ValueError("The selected area contains no source grid cells")
    return field


def _read_series(paths, preferred_names, bounds, date_start, duration):
    arrays = []
    for path in paths:
        with xr.open_dataset(path) as source:
            matches = [name for name in preferred_names if name in source.data_vars]
            if not matches and len(source.data_vars) == 1:
                matches = list(source.data_vars)
            if not matches:
                raise ValueError(f"No expected variable in {path}: {list(source.data_vars)}")
            field = _crop(_standardize_grid(source[matches[0]]), bounds)
            if "time" in field.coords and "time" not in field.dims:
                field = field.expand_dims("time")
            if "time" in field.dims:
                field = field.assign_coords(time=np.asarray(field.time.values).astype("datetime64[D]").astype("datetime64[ns]"))
            if "time" not in field.dims:
                raise ValueError(f"No time dimension in {path}")
            arrays.append(field.load())
    if not arrays:
        raise ValueError("No NetCDF files were provided")
    series = xr.concat(arrays, dim="time").sortby("time")
    return select_daily_window(series, date_start, duration)


def prepare_remote_inputs(tamsat_files, agera5_files, bounds, assets_dir,
                          date_start, duration):
    """Build a simulation-ready weather and soil Dataset from downloaded NetCDF."""
    _dates(date_start, duration)
    _bounds(bounds)
    rain = _read_series(tamsat_files, ("rfe_filled",), bounds,
                        date_start, duration).astype("float32")
    data = xr.Dataset({"rain": rain.transpose("time", "y", "x")})
    data.rio.write_crs("EPSG:4326", inplace=True)
    _describe_input_variables(data, "rain")
    data["rain"].attrs["source"] = "TAMSAT v3.1 rfe_filled"

    aliases = {
        "tpMoy": ("Temperature_Air_2m_Mean_24h", "2m_temperature_24_hour_mean",
                  "2m_temperature", "t2m"),
        "ET0": ("ReferenceET_PenmanMonteith_FAO56",
                "reference_evapotranspiration_penman_monteith_fao56", "ET0"),
        "rg": ("Solar_Radiation_Flux", "solar_radiation_flux", "rg"),
    }
    for name in ("tpMoy", "ET0", "rg"):
        field = _read_series(agera5_files[name], aliases[name],
                             _agera5_bounds(bounds), date_start, duration)
        # CDS AgERA5 v2 units: K, mm/day and J/m2/day, respectively.
        if name == "tpMoy":
            field = field - 273.15
        elif name == "rg":
            field = field / 1_000_000
        field = field.rio.write_crs("EPSG:4326").rio.reproject_match(
            data, resampling=Resampling.nearest, nodata=np.nan,
        )
        data[name] = field.transpose("time", "y", "x").astype("float32")
        missing = np.isfinite(data["rain"].values) & ~np.isfinite(data[name].values)
        if missing.any():
            raise ValueError(
                f"{name} has {int(missing.sum())} missing values on the TAMSAT grid; "
                "download AgERA5 with a wider area"
            )
        _describe_input_variables(data, name)
    data["tpMoy"].attrs["source"] = "AgERA5 v2 daily mean air temperature"
    data["ET0"].attrs.update(
        source="AgERA5 v2 Penman-Monteith FAO56",
        description="Daily reference evapotranspiration, Penman-Monteith FAO56.")
    data["rg"].attrs.update(
        source="AgERA5 v2 solar radiation flux",
        description="Daily solar radiation converted from J/m2/day to MJ/m2/day.")
    data = load_iSDA_soil_data(data, data.sizes["y"], data.sizes["x"],
                               assets_dir=assets_dir)
    validate_input_dataset(data, SimulationConfig(date_start, duration))
    return data
