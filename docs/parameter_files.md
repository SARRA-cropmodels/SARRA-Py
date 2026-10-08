# Parameter files

SARRA-Py uses three YAML mappings. The new `ModelParameters` object keeps these
mappings separate and `load_model_parameters` accepts explicit file paths. The
existing notebook loader remains available. The high-level API checks required
keys and value types before simulation; it does not yet impose agronomic ranges
or silently replace missing values with defaults.

| Mapping | Role | Representative fields |
|---|---|---|
| `variety` | Crop and cultivar response | `SDJLevee`, `SDJBVP`, `TBase`, `TOpt1`, `TOpt2`, `TLim`, `VRacBVP`, `kdf`, `kcMax`, `KRdtPotA` |
| `management` | Sowing, density, irrigation and mulch | `DateSemis`, `densite`, `irrigAuto`, `maxIrrig`, `biomIniMc`, `humSatMc`, `NI` |
| `soil` | Legacy soil-parameter mapping | Existing `data/params/soil/*.yaml` files |

The reference files are under `data/params/variety`, `data/params/itk` and
`data/params/soil`. All current reference variety and management YAML files
contain the keys required by `run_simulation`. Extra keys remain allowed for
notebook compatibility. The complete required-key sets are defined as
`REQUIRED_VARIETY` and `REQUIRED_MANAGEMENT` in `sarra_py.api`.

`DateSemis` must be an ISO date such as `2020-05-01`. `irrigAuto` must be a
boolean; other required management values and all required variety values must
be numeric. `NI` may be `.nan`, preserving the established optional
intensification behavior.

The spatial soil fields used by the current daily model come from the input
`xarray.Dataset`, not from the `soil` YAML mapping. This distinction matters
when preparing a run: providing a soil YAML alone does not supply the gridded
`ru`, reservoir stocks, depths or runoff fields. The [API and CLI guide](usage_api_cli.md#input-contract) lists these dataset fields.

The model updates internal parameter copies where its existing equations
require it. A `ModelParameters` instance supplied to `run_simulation` is not
modified. Parameter units and scientific interpretation belong in
[Model formalisms](model_formalisms.md); unresolved scientific choices belong
in [Scientific validation questions](scientific_validation_questions.md).
