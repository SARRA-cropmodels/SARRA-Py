# Spatialization strategy

SARRA-Py simulates a daily crop state at every cell of one spatial grid. The
weather, soil fields, intermediate state and outputs share an `xarray.Dataset`.
Daily variables normally have `(time, y, x)` dimensions and soil fields have
`(y, x)`. The API also accepts `(time, x, y)` when all daily variables use
that order consistently. See the [input contract](usage_api_cli.md#input-contract)
for required fields and units.

## Choosing the calculation grid

The input dataset defines the calculation grid. In the GeoTIFF workflow of
Example 1, the TAMSAT rainfall loader establishes the dates and grid; the
AgERA5 climate and soil loaders align their fields to it. The climate product
does not determine the output resolution in that workflow. A caller using a
prepared NetCDF or assembling a dataset in memory may choose another grid,
provided the input contract is met. `run_simulation` does not resample or
reproject a prepared dataset during the simulation.

The spatial resolution of an output therefore describes the calculation grid,
not necessarily the native information content of every input. Resampling a
coarser weather or soil product does not add spatial detail to that product.
Document the chosen grid, source resolutions and alignment method when
interpreting maps or comparing runs.

## Daily state and outputs

Each daily step reads the current weather and model state, then updates water,
phenology and carbon variables in the order documented in
[Model formalisms](model_formalisms.md#state-and-time-step). The result is an
`xarray.Dataset` with daily and spatial coordinates, including intermediate
diagnostics. Spatial summaries and maps can be derived from those outputs,
with appropriate treatment of missing cells and grid-cell area.

The selected calculation engine affects execution, not the output container:
both `engine="numpy"` (the current default) and `engine="xarray"` return an
`xarray.Dataset`. The full daily state is retained, so memory use grows with
the number of cells, days and stored variables. For first runs, select a small
spatial window or short period as shown in the [example notebooks](notebook_examples.md).
Measure your workload on the intended machine and grid; see
[Performance checks](usage_api_cli.md#performance-checks).
