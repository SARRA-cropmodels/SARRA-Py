# Example notebooks

Run notebooks from the `notebooks/` directory so that their
`../data/` paths resolve. Install the project and dependencies
first using the instructions in [the README](../README.md). Each runnable
example now builds a weather and soil `xarray.Dataset`, loads
validated YAML parameters, and calls the same public
`run_simulation(data, parameters, SimulationConfig(...))` entry point
used by the CLI. The public default remains `engine="xarray"`.

| Example | Workflow |
|---|---|
| 1 | One millet crop and spatial yield maps |
| 2 and 2 Victor | Parameter optimization against measured yield |
| 3 | Search for the best sowing date |
| 4 | Search for phenological phase lengths |
| 5 | Compare modeled vegetation dynamics with MODIS LAI |
| 6 | Compare rainfall products |
| 7–9 | Run prepared NetCDF weather grids |
| 10 | Run one climate model over multiple years |
| 11 | Run all complete climate model triplets in a directory |
| 12 | Compare rainfall and temperature scenarios |
| 13 | Download TAMSAT and AgERA5 NetCDF data and simulate Niger millet |
| Grid example 2 | Run the water balance model on a sowing date grid |
| Example xx | Bayesian parameter calibration |

The notebooks retain their preparation and visualization code. Scenario and
optimization loops create an independent parameter mapping for each run;
NetCDF examples use `select_daily_window` to check date coverage.
This allows a notebook to alter weather, soil grids, sowing dates and variety
values in memory without writing a CLI configuration file.

Examples 1, 3, 4 and 5 require additional input files absent from this
checkout. Example 11 defaults to the complete climate triplet included under
`data/exemple_data/exemple_10`; set `CLIMATE_DIR` to a larger
collection to analyze multiple models. Example 8 uses its local NetCDF files
and does not require a CDS download. Example 12's full grid and four scenario
runs can need substantial memory; reduce the `y` and `x` extent
while experimenting.

The [API guide](usage_api_cli.md) lists the required variable names, units and
dimensions. `run_simulation` verifies the time axis and required fields
before the daily loop. CF calendars lacking requested Gregorian dates must be
handled by selecting a compatible season or preparing a Gregorian daily series.

## Download-to-simulation example

`notebooks/SARRA-Py - Example 13 - Download and simulate Niger millet.ipynb` downloads TAMSAT v3.1 daily rainfall NetCDFs and AgERA5 v2 climate NetCDFs, prepares a weather and soil dataset, then runs the public simulation API. The AgERA5 downloader needs CDS API credentials and accepted dataset terms. Downloads are cached under `data/exemple_data/exemple_13/` by date range and geographic box. This notebook uses AgERA5 v2 Penman–Monteith ET0; Example 1 uses archived Hargreaves ET0 GeoTIFFs, so their results need not match.

The reusable functions are `download_tamsat_daily`, `download_agera5_v2`, and `prepare_remote_inputs`. `prepare_remote_inputs` takes explicit paths to soil assets and returns the same variable contract accepted by `run_simulation` and the `prepared_netcdf` CLI mode.
