"""File-based application layer shared by Python callers and the CLI."""

from datetime import date
from pathlib import Path

import xarray as xr
import yaml

from .api import SimulationConfig, load_model_parameters, override_parameters, run_simulation
from .data_preparation import load_AgERA5_data, load_TAMSAT_data


def load_tamsat_agera5(rainfall_dir, climate_dir, soil_dataset, date_start, duration, progress=False):
    """Load dated weather TIFFs and merge soil on the same spatial grid.

    Return a prepared Dataset; soil_dataset must have exactly matching
    coordinates."""
    data = xr.Dataset()
    data = load_TAMSAT_data(data, str(rainfall_dir), date_start, duration)
    data = load_AgERA5_data(data, str(climate_dir), date_start, duration, progress=progress)
    with xr.open_dataset(soil_dataset) as soil:
        data = xr.merge((data, soil.load()), join="exact")
    return data


def _mapping(value, name):
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a YAML mapping")
    return value


def _path(base, value, name):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty path")
    path = Path(value).expanduser()
    return (path if path.is_absolute() else base / path).resolve()


def execute_config(config_path, overwrite=False):
    """Run a YAML configuration and return the written NetCDF path.

    Resolve input and output paths relative to the configuration file;
    overwrite must be true to replace an existing output."""
    config_path = Path(config_path).expanduser().resolve()
    with config_path.open(encoding="utf-8") as stream:
        document = _mapping(yaml.safe_load(stream), "configuration")
    base = config_path.parent
    simulation = _mapping(document.get("simulation"), "simulation")
    inputs = _mapping(document.get("input"), "input")
    parameters = _mapping(document.get("parameters"), "parameters")
    output = _mapping(document.get("output"), "output")

    try:
        start = date.fromisoformat(str(simulation["date_start"]))
    except (KeyError, ValueError) as exc:
        raise ValueError("simulation.date_start must be an ISO date") from exc
    spec = SimulationConfig(
        date_start=start,
        duration=simulation.get("duration"),
        engine=simulation.get("engine", "numpy"),
        model=simulation.get("model", "full"),
        progress=simulation.get("progress", False),
    )
    spec.validate()
    parameter_set = load_model_parameters(
        _path(base, parameters.get("variety"), "parameters.variety"),
        _path(base, parameters.get("management"), "parameters.management"),
        _path(base, parameters.get("soil"), "parameters.soil"),
    )
    if "overrides" in parameters:
        changes = _mapping(parameters["overrides"], "parameters.overrides")
        unknown = sorted(set(changes) - {"variety", "management", "soil"})
        if unknown:
            raise ValueError(f"Unknown parameter override groups: {', '.join(unknown)}")
        parameter_set = override_parameters(
            parameter_set,
            **{name: _mapping(value, f"parameters.overrides.{name}")
               for name, value in changes.items()},
        )

    output_path = _path(base, output.get("path"), "output.path")
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output exists: {output_path}; use --overwrite to replace it")

    kind = inputs.get("kind")
    if kind == "prepared_netcdf":
        input_path = _path(base, inputs.get("path"), "input.path")
        with xr.open_dataset(input_path) as opened:
            data = opened.load()
        result = run_simulation(data, parameter_set, spec)
    elif kind == "tamsat_agera5":
        data = load_tamsat_agera5(
            _path(base, inputs.get("rainfall_dir"), "input.rainfall_dir"),
            _path(base, inputs.get("climate_dir"), "input.climate_dir"),
            _path(base, inputs.get("soil_dataset"), "input.soil_dataset"),
            spec.date_start,
            spec.duration,
            progress=spec.progress,
        )
        result = run_simulation(data, parameter_set, spec)
    else:
        raise ValueError("input.kind must be 'prepared_netcdf' or 'tamsat_agera5'")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_netcdf(output_path)
    return output_path
