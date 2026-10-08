# Software architecture

SARRA-Py simulates a daily crop state on a spatial grid. One `xarray.Dataset`
carries weather, soil fields, model state and outputs. The public Python API and
CLI use the same model functions that existing notebooks call.

## Layers

| Layer | Main module | Responsibility |
|---|---|---|
| Data preparation | `data_preparation.py` | Read dated TAMSAT/AgERA5 rasters, build soil fields and day length |
| Input contract | `api.py` | Represent options and parameter groups; validate dates, fields and dimensions |
| Application | `application.py` | Resolve YAML paths, load NetCDF or TIFF inputs, write NetCDF output |
| Calculation | `models.py` and `bilan_*.py` | Initialize and advance phenology, water and carbon balances |
| Command line | `cli.py`, `__main__.py` | Parse a configuration path and call the application layer |

The route is:

`CLI configuration → input and parameter loading → run_simulation → existing
model loop → NetCDF result`

Python callers can start at `run_simulation` with an in-memory dataset and
`ModelParameters`. The CLI calls this same function through `execute_config`.
Lower-level notebook imports from `sarra_py` remain available.

## Data and state

Weather variables have dimensions `(time, y, x)` or `(time, x, y)`. Soil fields
use the matching spatial dimensions. Each model step reads the current and
previous daily slices and writes state into the result dataset. The API copies
caller inputs before initialization and passes copies of parameter mappings to
the established model loop.

The default engine is `xarray`. `engine="numpy"` selects the existing NumPy
daily loop through the same API; the output remains an `xarray.Dataset`.
The two engine outputs are compared in the reproducible benchmarks. Scientific
equations and their validation status are documented in
[Model formalisms](model_formalisms.md).

## Input boundaries and limits

A prepared NetCDF supplies weather and spatial soil fields. The TIFF route
reads dated rainfall and climate files and merges a soil NetCDF already on the
rainfall grid. The loaders require every requested date and reject duplicates.
The [API and CLI guide](usage_api_cli.md) defines exact fields and units.
Parameter YAMLs are grouped as described in
[Parameter files](parameter_files.md).

The API checks field presence, dimension order, date alignment and required
parameter types. It does not currently validate all physical ranges, units or
missing-value patterns. The existing daily loop stores many intermediate arrays
for diagnostics, which increases memory use with grid size and simulation
duration. See the performance baseline in `docs/dev/audits` for measured
engine timings and remaining work.
