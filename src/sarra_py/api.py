"""Validated, notebook-compatible entry point for a SARRA-Py simulation."""

from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from numbers import Real
from pathlib import Path
from typing import Mapping

import numpy as np
import xarray as xr

from .bilan_carbo import initialize_simulation
from .bilan_pheno import calculate_once_daily_thermal_time
from .data_preparation import (
    calc_day_length_raster_fast,
    initialize_default_irrigation,
    load_YAML_parameters,
)
from .models import run_model, run_waterbalance_model


REQUIRED_VARIETY = frozenset("""
    AGauss KRdtBiom KRdtPotA KRdtPotB LGauss NIYo NIp PFactor PPCrit PPExp
    PPsens SDJBVP SDJLevee SDJMatu1 SDJMatu2 SDJRPR SeuilPP TBase TLim
    TOpt1 TOpt2 VRacBVP VRacLevee VRacMatu1 VRacMatu2 VRacPSP VRacRPR
    aeroTotBase aeroTotPente densOpti densiteA densiteP feuilAeroBase
    feuilAeroPente kRespMaint kcMax kdf pcReallocFeuille phaseDevVeg
    poidsSecGrain seuilCstrMortality slaMax slaMin slaPente tempMaint
    txAssimBVP txAssimMatu1 txAssimMatu2 txConversion txRealloc txResGrain
""".split())
REQUIRED_MANAGEMENT = frozenset("""
    DateSemis KI KNLit KNUp KT NI biomIniMc coefMc densite humSatMc
    irrigAuto irrigAutoTarget maxIrrig mulch nbjTestSemis profRacIni
    seuilEauSemis surfMc
""".split())
REQUIRED_WEATHER = ("rain", "tpMoy", "ET0", "rg")
REQUIRED_SOIL = (
    "ru", "epaisseurSurf", "epaisseurProf", "profRu", "stockIniProf", "stockIniSurf",
    "runoff_threshold", "runoff_rate",
)


@dataclass(frozen=True)
class ModelParameters:
    """Variety, management and soil parameter mappings for one simulation."""

    variety: Mapping
    management: Mapping
    soil: Mapping


@dataclass(frozen=True)
class SimulationConfig:
    """Simulation dates and execution options; NumPy is the default engine."""

    date_start: date
    duration: int
    engine: str = "numpy"
    model: str = "full"
    progress: bool = False

    def validate(self):
        if isinstance(self.date_start, datetime) or not isinstance(self.date_start, date):
            raise ValueError("date_start must be a date")
        if not isinstance(self.duration, int) or isinstance(self.duration, bool) or self.duration <= 0:
            raise ValueError("duration must be a positive integer")
        if self.engine not in ("xarray", "numpy"):
            raise ValueError("engine must be 'xarray' or 'numpy'")
        if self.model not in ("full", "waterbalance"):
            raise ValueError("model must be 'full' or 'waterbalance'")
        if not isinstance(self.progress, bool):
            raise ValueError("progress must be boolean")


def load_model_parameters(variety_path, management_path, soil_path):
    """Load variety, management and soil YAML files from explicit paths.

    Return validated ModelParameters; paths may be absolute or relative to
    the current working directory."""
    paths = [str(Path(path).expanduser().resolve()) for path in
             (variety_path, management_path, soil_path)]
    variety, management, soil = load_YAML_parameters(*paths)
    parameters = ModelParameters(variety, management, soil)
    validate_parameters(parameters)
    return parameters


def validate_parameters(parameters):
    """Check required keys and value types in a ModelParameters object."""
    if not isinstance(parameters, ModelParameters):
        raise TypeError("parameters must be a ModelParameters instance")
    for label, values, required in (
        ("variety", parameters.variety, REQUIRED_VARIETY),
        ("management", parameters.management, REQUIRED_MANAGEMENT),
    ):
        if not isinstance(values, Mapping):
            raise ValueError(f"{label} parameters must be a mapping")
        missing = sorted(required - values.keys())
        if missing:
            raise ValueError(f"Missing {label} parameters: {', '.join(missing)}")
    if not isinstance(parameters.soil, Mapping):
        raise ValueError("soil parameters must be a mapping")
    for key in REQUIRED_VARIETY:
        value = parameters.variety[key]
        if not isinstance(value, Real) or isinstance(value, bool):
            raise ValueError(f"variety parameter {key} must be numeric")
    sowing_date = parameters.management["DateSemis"]
    if isinstance(sowing_date, str):
        try:
            date.fromisoformat(sowing_date)
        except ValueError as exc:
            raise ValueError("DateSemis must be an ISO date") from exc
    elif not isinstance(sowing_date, date):
        raise ValueError("DateSemis must be a date or ISO date string")
    for key in REQUIRED_MANAGEMENT - {"DateSemis", "irrigAuto"}:
        value = parameters.management[key]
        if not isinstance(value, Real) or isinstance(value, bool):
            raise ValueError(f"management parameter {key} must be numeric")
    if not isinstance(parameters.management["irrigAuto"], bool):
        raise ValueError("management parameter irrigAuto must be boolean")


def override_parameters(parameters, *, variety=None, management=None, soil=None):
    """Return a validated parameter copy with selected values replaced."""
    validate_parameters(parameters)
    updated = {}
    for name, changes in (
        ("variety", variety), ("management", management), ("soil", soil),
    ):
        original = getattr(parameters, name)
        values = deepcopy(dict(original))
        if changes is not None:
            if not isinstance(changes, Mapping):
                raise TypeError(f"{name} overrides must be a mapping")
            unknown = sorted(set(changes) - set(values), key=str)
            if unknown:
                raise ValueError(
                    f"Unknown {name} parameters: {', '.join(map(str, unknown))}"
                )
            values.update(deepcopy(dict(changes)))
        updated[name] = values

    sowing_date = updated["management"]["DateSemis"]
    if isinstance(sowing_date, str):
        try:
            updated["management"]["DateSemis"] = date.fromisoformat(sowing_date)
        except ValueError as exc:
            raise ValueError("DateSemis must be an ISO date") from exc
    elif isinstance(sowing_date, datetime):
        updated["management"]["DateSemis"] = sowing_date.date()

    result = ModelParameters(**updated)
    validate_parameters(result)
    return result


def select_daily_window(data, date_start, duration):
    """Return exactly duration daily values starting at date_start.

    Accept datetime64 or CF calendars when every requested Gregorian day
    exists; raise ValueError for missing or duplicate days."""
    if not isinstance(data, (xr.Dataset, xr.DataArray)):
        raise TypeError("data must be an xarray Dataset or DataArray")
    if not isinstance(date_start, date) or isinstance(date_start, datetime):
        raise ValueError("date_start must be a date")
    if not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0:
        raise ValueError("duration must be a positive integer")
    if "time" not in data.coords:
        raise ValueError("data must have a time coordinate")

    from datetime import timedelta

    date_end = date_start + timedelta(days=duration - 1)
    window = data.sel(time=slice(date_start.isoformat(), date_end.isoformat()))
    values = np.asarray(window["time"].values)
    if np.issubdtype(values.dtype, np.datetime64):
        observed = values.astype("datetime64[D]").astype(str).tolist()
    else:
        try:
            observed = [f"{item.year:04d}-{item.month:02d}-{item.day:02d}" for item in values]
        except AttributeError as exc:
            raise ValueError("time coordinates must contain dates") from exc
    expected = [(date_start + timedelta(days=i)).isoformat() for i in range(duration)]
    if observed != expected:
        raise ValueError("Selected time window must contain every Gregorian day exactly once")
    return window.assign_coords(time=np.asarray(expected, dtype="datetime64[ns]"))


def validate_input_dataset(data, config):
    """Check a prepared weather and soil grid against the simulation dates.

    Required names, dimension order, numeric types and daily time coordinates
    are checked; physical units are documented separately."""
    config.validate()
    if not isinstance(data, xr.Dataset):
        raise TypeError("data must be an xarray.Dataset")
    missing = sorted(set(REQUIRED_WEATHER + REQUIRED_SOIL) - set(data.data_vars))
    if missing:
        raise ValueError(f"Missing input variables: {', '.join(missing)}")
    rain = data["rain"]
    if len(rain.dims) != 3 or rain.dims[0] != "time" or set(rain.dims[1:]) != {"x", "y"}:
        raise ValueError("rain dimensions must be ('time', 'y', 'x') or ('time', 'x', 'y')")
    if rain.sizes["time"] != config.duration:
        raise ValueError("rain time length must equal duration")
    for name in REQUIRED_WEATHER + ("dureeDuJour", "irrigation"):
        if name in data and data[name].dims != rain.dims:
            raise ValueError(f"{name} dimensions must match rain dimensions {rain.dims}")
    for name in REQUIRED_SOIL:
        if data[name].dims != rain.dims[1:]:
            raise ValueError(f"{name} dimensions must match rain spatial dimensions {rain.dims[1:]}")
    for name in REQUIRED_WEATHER + REQUIRED_SOIL + ("dureeDuJour", "irrigation"):
        if name in data and data[name].dtype.kind not in "iuf":
            raise ValueError(f"{name} must contain real numeric values")
    if "time" in data.coords:
        values = np.asarray(data["time"].values)
        if np.issubdtype(values.dtype, np.datetime64):
            expected = np.datetime64(config.date_start.isoformat(), "D") + np.arange(config.duration)
            if not np.array_equal(values.astype("datetime64[D]"), expected):
                raise ValueError("time coordinates must match date_start and duration, day by day")
        elif values.dtype.kind not in "iu" or not np.array_equal(values, np.arange(config.duration)):
            raise ValueError("time coordinates must be Gregorian dates or consecutive indices from zero")


def run_simulation(data, parameters, config):
    """Run a full or water balance simulation from a prepared xarray grid.

    Validate inputs, initialize an independent state and return its dataset.
    Missing day length and irrigation are derived from the grid when possible."""
    validate_input_dataset(data, config)
    validate_parameters(parameters)
    variety = deepcopy(dict(parameters.variety))
    management = deepcopy(dict(parameters.management))
    soil = deepcopy(dict(parameters.soil))
    if isinstance(management["DateSemis"], str):
        management["DateSemis"] = date.fromisoformat(management["DateSemis"])
    elif isinstance(management["DateSemis"], datetime):
        management["DateSemis"] = management["DateSemis"].date()
    prepared = data.copy(deep=True)
    if "dureeDuJour" not in prepared:
        crs = prepared.rio.crs
        if crs is not None and not crs.is_geographic:
            raise ValueError("day length requires geographic y coordinates or supplied dureeDuJour")
        latitudes = np.asarray(prepared["y"].values, dtype=float)
        if not np.isfinite(latitudes).all() or np.any(np.abs(latitudes) > 90):
            raise ValueError("y must contain latitudes in degrees to compute day length")
        prepared = calc_day_length_raster_fast(prepared, config.date_start, config.duration)
    if "irrigation" not in prepared:
        prepared = initialize_default_irrigation(prepared)
    prepared = initialize_simulation(
        prepared, prepared["rain"].shape[1], prepared["rain"].shape[2],
        config.duration, variety, management, config.date_start,
    )
    prepared = calculate_once_daily_thermal_time(prepared, variety)
    runner = run_model if config.model == "full" else run_waterbalance_model
    return runner(variety, management, soil, prepared, config.duration,
                  engine=config.engine, progress=config.progress)
