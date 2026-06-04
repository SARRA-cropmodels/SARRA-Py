# SARRA-Py performance refactor plan

## Notebook API observed

Existing notebooks import the package with `from sarra_py import *` and keep the
model logic in the package. The recurring public calls are:

- `get_grid_size`
- `load_TAMSAT_data`
- `load_AgERA5_data`
- `load_iSDA_soil_data`
- `load_iSDA_soil_data_alternate`
- `calc_day_length_raster_fast`
- `load_YAML_parameters`
- `initialize_simulation`
- `initialize_default_irrigation`
- `calculate_once_daily_thermal_time`
- `run_model`
- `run_waterbalance_model`

These names must stay importable from `sarra_py`.

## Hot path

The slow core is the daily loop in `src/sarra_py/models.py`. For each day,
`run_model` chains phenology, water balance and carbon balance functions. Those
functions repeatedly write into an `xarray.Dataset`.

The most expensive patterns are:

- repeated `xr.where` inside daily functions
- repeated writes like `data["var"][j:, :, :] = ...`
- repeated `data["var"][j, :, :]` xarray indexing at every step
- repeated xarray alignment/broadcasting for variables that are already on the
  same grid
- `xr.concat` in raster loading helpers, outside the simulation loop

## Minimal refactor path

1. Keep notebook inputs and outputs as `xarray.Dataset`.
2. Keep `run_model` and `run_waterbalance_model` as the public entry points.
3. Add an internal NumPy engine:
   - materialize each `DataArray` once at the start of the run
   - run the existing daily logic on a mapping of `np.ndarray`
   - restore arrays into the original `Dataset` at the end
4. Keep the legacy xarray engine available with `engine="xarray"` for
   regression tests and benchmarks.
5. Move additional `xr.where` calls to `np.where` only after equivalence tests
   cover them.
6. Add optional output filtering later, with a default that keeps all existing
   daily variables.
7. Consider Numba only after the NumPy engine is stable and tested.

## Implemented first step

`run_model` and `run_waterbalance_model` accept `engine="numpy"` for the fast
internal path while keeping `engine="xarray"` as the public default until the
realistic notebook validation is complete.

`calculate_once_daily_thermal_time` and `calculate_daily_thermal_time` now use
NumPy for the thermal-time formula while preserving their public names.
