# Changelog

## 0.2.0 — 2026-10-22

This release unifies simulation entry points and documents scientific and
numerical corrections. Results can change for the affected scenarios below.

### Added

- A shared Python API and YAML-driven CLI for validated simulation inputs.
- Parameter overrides for notebook scenarios and command-line runs.
- TAMSAT and AgERA5 download/preparation helpers and a download-to-simulation notebook.
- Updated example notebooks.
- Markdown documentation for inputs, model formalisms and scientific questions.
- Optional `notebooks` and `dev` dependency groups.
- Shared package version exposed by `sarra_py.__version__` and `sarra-py --version`.

### Changed

- NumPy is the default calculation engine. Outputs remain xarray datasets.
- Rainfall loaders check date coverage; input variables carry descriptive metadata.
- Standalone packaging now uses a setuptools build backend. Source archives
  include the requirement files needed to build a wheel.

### Scientific and numerical corrections

- Transpiration is capped by the root water stock available after evaporation.
- `Ncrit` is undefined (`NaN`) for zero or negative biomass.
- Runoff is bounded between zero and the nonnegative water
  remaining after mulch interception. The rainfall threshold remains the trigger.
  This corrects artificial water addition caused by negative runoff under mulch.
  See [Model formalisms](docs/model_formalisms.md#runoff-drainage-and-crop-residue-mulch).

- Prescribed irrigation is applied independently of automatic scheduling.
  The automatic reservoir-filling dose rule is retained.
- Initial surface storage uses `stockIniSurf`; total storage includes both
  surface and deeper initial stocks, without double counting root storage.
- Both TAMSAT GeoTIFF loaders decode declared NoData to `NaN`, without filling
  missing rainfall with zero.
- Phase 6 now uses `VRacMatu2` instead of inheriting the phase-5 root speed.
  These changes can affect irrigation, sowing and crop development; see the
  [documented behaviour](docs/model_formalisms.md#water-input-and-root-growth-conventions).

- Management YAML accepts both quoted date strings and native YAML dates or
  timestamps for `DateSemis`, consistently with the public API.

### Example analysis corrections

- Example 6 imports pandas; Example 8 defines its simulation-year bounds.
- Examples 8 and 10 use a conservative default worker count for climate runs.
- Example 5 exports optimization results through the public `optimizer.res`
  interface.

- Examples 10/11 label their ordinary Mann-Kendall diagnostic accurately;
  Example 10 includes the required normal-distribution import.

### Known limitations under discussion

- Scientific source matching and validation remain open for some formalisms.
  See [Scientific validation questions](docs/scientific_validation_questions.md).
- The full set of example notebooks has not been rerun for this release.
  Prepared climate collections required by some examples are supplied separately.
