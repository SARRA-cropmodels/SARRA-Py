# Python API and command line

SARRA-Py can run from a prepared `xarray.Dataset` or from a YAML configuration.
Both routes call `run_simulation`; the command line contains no separate model
calculation. The existing notebook functions, including `run_model`, remain
available. `engine="numpy"` is the default in both interfaces.

## Python API

```python
from datetime import date
import xarray as xr
from sarra_py import (
    SimulationConfig,
    load_model_parameters,
    run_simulation,
)

parameters = load_model_parameters(
    "data/params/variety/millet_variety.yaml",
    "data/params/itk/millet_niger_2017.yaml",
    "data/params/soil/USA_iowa_V42.yaml",
)
config = SimulationConfig(date_start=date(2016, 5, 1), duration=120)
with xr.open_dataset("prepared_inputs.nc") as inputs:
    result = run_simulation(inputs, parameters, config)
    result.to_netcdf("simulation.nc")
```

`run_simulation` validates the input contract, copies the input dataset, adds
day length and zero irrigation if absent, initializes the model state, computes
daily thermal time, and runs the selected model. It does not mutate the caller's
input dataset or parameter mappings. Use `model="waterbalance"` for the reduced
model and `engine="xarray"` to select the xarray engine.

For notebooks, load or build any weather and soil grid as an in-memory
`xarray.Dataset`. The runner has no dependency on a particular file
layout. Slice a dated source with `select_daily_window(source, start, duration)`
before combining it with other variables. This helper checks every requested
Gregorian day and converts compatible CF calendars; it rejects windows that
omit a Gregorian leap day.

To compare sowing dates, varieties or climate scenarios, create a new
`ModelParameters` object or modify a copy of the base dataset for each
run. For example:

```python
from sarra_py import SimulationConfig, override_parameters, run_simulation

outputs = {}
for name, rainfall_factor in {"baseline": 1.0, "dry": 0.8}.items():
    scenario = inputs.copy(deep=True)
    scenario["rain"] = scenario["rain"] * rainfall_factor
    scenario_parameters = override_parameters(
        parameters, management={"DateSemis": date(2023, 5, 1)},
    )
    outputs[name] = run_simulation(
        scenario, scenario_parameters, SimulationConfig(date(2023, 4, 1), 120),
    )
```

`override_parameters` also accepts `variety` and `soil` mappings. It makes an
independent copy, rejects unknown parameter names, normalizes `DateSemis`, and
validates the result. The original YAML files and parameter object are unchanged.
The same API handles optimization loops and `model="waterbalance"`.
See [the example notebooks](notebook_examples.md) for local input files and
the individual workflows.

The lower-level `run_model` and `run_waterbalance_model` functions still accept
an already initialized dataset and retain their notebook-facing signatures.
Scientific equations are described in [Model formalisms](model_formalisms.md).

## Command line

Install the package with `pip install .`, then run:

```bash
sarra-py run.yaml
# equivalent: python -m sarra_py run.yaml
```

A configuration for an already prepared NetCDF dataset:

```yaml
input:
  kind: prepared_netcdf
  path: prepared_inputs.nc
parameters:
  variety: data/params/variety/millet_variety.yaml
  management: data/params/itk/millet_niger_2017.yaml
  soil: data/params/soil/USA_iowa_V42.yaml
  overrides:
    variety:
      TBase: 12.0
    management:
      DateSemis: "2016-05-02"
simulation:
  date_start: 2016-05-01
  duration: 120
  engine: numpy
  model: full
  progress: false
output:
  path: results/millet.nc
```

For date-coded TAMSAT and AgERA5 GeoTIFF directories, use:

```yaml
input:
  kind: tamsat_agera5
  rainfall_dir: rainfall_tiffs
  climate_dir: agera5_tiffs
  soil_dataset: soil_on_rainfall_grid.nc
parameters:
  variety: variety.yaml
  management: management.yaml
  soil: soil.yaml
simulation:
  date_start: 2020-05-01
  duration: 120
output:
  path: results/run.nc
```

All paths in the configuration are resolved relative to `run.yaml`. Optional
`parameters.overrides` uses the same copy and validation function as Python;
omit it to use the YAML values unchanged. `simulation.date_start` selects the
first input day, while `management.DateSemis` is the sowing date. The soil
NetCDF must already be on the rainfall grid. An existing output is protected;
pass `--overwrite` to replace it. The command prints the output path on success.
Set `simulation.progress: true` to show model and raster-loading progress.

## Input contract

The base dataset contains daily variables on `(time, y, x)` or `(time, x, y)`.
The first dimension must be `time`, and every daily variable must have exactly
the same dimension order as `rain`. Soil variables have the two spatial
dimensions in that same order.

| Daily variable | Meaning | Expected unit |
|---|---|---|
| `rain` | Rainfall | mm per day |
| `tpMoy` | Mean air temperature | degrees C |
| `ET0` | Reference evapotranspiration | mm per day |
| `rg` | Solar radiation | MJ m-2 per day |
| `dureeDuJour` | Day length; optional if `y` contains latitude | hours |
| `irrigation` | Irrigation; optional, defaults to zero | mm per day |

Required spatial variables are `ru`, `epaisseurSurf`, `epaisseurProf`, `profRu`,
`stockIniProf`, `stockIniSurf`, `runoff_threshold`, and `runoff_rate`.
The soil variables and their scientific meaning are described in
[Model formalisms](model_formalisms.md). `time` may contain consecutive
Gregorian dates matching `date_start`, or integer indices from zero. When day
length is absent, `y` must be latitude in degrees. The input contract checks
names, numeric types, dimensions and calendar alignment; it does not currently verify physical
units or all missing-value patterns.

The GeoTIFF loaders require one TIFF per requested day and reject missing or
duplicate dates. They assign actual daily coordinates to rainfall and climate
series. The AgERA5 adapter maps the local mean-temperature, Hargreaves ET0 and
solar-radiation folders to `tpMoy`, `ET0` and `rg`; it divides local radiation
values by 1000 as in the notebook workflow. That conversion assumes the local
TIFFs contain kJ m-2 per day.

## Parameters

`load_model_parameters` accepts explicit paths, validates required keys and
returns a `ModelParameters` object containing `variety`, `management` and `soil`
mappings. `DateSemis` is an ISO date in the management YAML. Numerical values
are passed to the established model equations without conversion. The model
may update internal copies of some parameters during a run; the supplied
mappings remain unchanged.

The public loader accepts the existing YAML files. For direct API use, a caller
may also construct `ModelParameters(variety, management, soil)` from mappings.
Missing or malformed required values fail before the daily loop. See
[Parameter files](parameter_files.md) for the grouping of inputs.

## Performance checks

Use `python benchmarks/benchmark_run_model.py --duration 45 --width 8
--height 7 --repeats 3` to compare the daily loops, or
`python benchmarks/benchmark_api.py --duration 45 --width 8 --height 7
--repeats 2` for a complete API run including validation and initialization.
Both benchmarks check output equivalence. Benchmark results depend on grid size,
duration and available memory; record all three with timings. A measured
baseline and limitations are in [the performance audit](dev/audits/2026-10-08-performance-baseline.md).
