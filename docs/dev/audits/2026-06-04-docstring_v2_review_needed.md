# Docstring V2 Review Needed

Date: 2026-06-04

This file lists functions whose docstrings were not changed during the
bibliography/docstring v2 pass because a direct scientific wording could hide
an unresolved ambiguity. Proposed docstrings below are review material only and
were not applied to the code.

## Review Table

| Functions | Why not modified | Proposed wording status | Validation question |
|---|---|---|---|
| `calculate_daily_thermal_time`, `calculate_once_daily_thermal_time` | The active code uses `tpMoy`, while historical comments mention a Tmin/Tmax formulation. | Keep existing cautious docstrings until the intended thermal-time formalism is confirmed. | Is the mean-temperature piecewise response the validated SARRA-Py formalism, or a temporary simplification? |
| `update_photoperiodism` | Dingkuhn et al. (2008) supports the "Impatience" model family, but the exact `sumPP` equation and thresholds need SARRA validation. | Could mention "related to the Impatience family" but not "implements Dingkuhn et al." | Are `PPExp`, `PPsens`, `PPCrit`, `SeuilPP` and the reset to 100 the intended operational rule? |
| `MortaliteSarraV3` | Mortality thresholds are parameter-driven and partly legacy; source mapping is not complete. | Keep factual, cautious wording. | Which mortality rules are validated for current crops and notebooks? |
| `EvolRurCstr2`, `initialize_delta_root_tank_capacity`, `update_delta_root_tank_capacity`, `update_root_tank_capacity`, `update_root_tank_stock` | Root capacity, root stock and humectation-front logic are tightly coupled. Internal comments already question `update_root_tank_stock`. | A docstring should describe active code but explicitly mark the mass-balance concern. | Does increasing `root_tank_stock` by `delta_root_tank_capacity` represent newly accessible stored water, or is it a legacy bug? |
| `fill_tanks`, `rempliRes`, `apply_humectation_front_boundaries`, multi-cycle tank helpers | Several functions propagate state from `j:` and include second-cycle logic that appears rare and complex. | Proposed only after reservoir invariants and water mass balance tests exist. | Are multi-cycle water carry-over rules still required? |
| `estimate_runoff`, `compute_runoff` | Condition uses `rain`, calculation uses `available_water` after irrigation/mulch. No source matched the exact rule. | Could document active rule, but should not imply hydrological validation. | Should runoff threshold be triggered by rain only, or by post-mulch `available_water`? |
| `compute_water_captured_by_mulch`, `estimate_FEMcW_and_update_mulch_water_stock`, mulch legacy functions | Unit conversions `/1000` and `/10000` are partly explained by comments but no strong source was verified. Division by zero warnings are known. | Leave as review until mulch source/calibration is confirmed. | Are mulch biomass, `surfMc`, `humSatMc` and FEMcW equations validated for current scenarios? |
| `update_plant_transpiration` and downstream `ConsoResSep` helpers | The active bound `tr = max(root_tank_stock - tr, 0)` looks scientifically suspicious; changing it would alter results. | Do not improve docstring beyond factual warning without validation. | Should transpiration be capped by available root stock (`min`) rather than transformed by the current residual expression? |
| `load_iSDA_soil_data`, `load_iSDA_soil_data_alternate` | Dataset sources are identifiable, but local adapted rasters, texture classes and CSV parameter mapping are project-specific. | Document as data-preparation provenance after confirming local asset lineage. | Which local soil parameter table is authoritative, and what units are guaranteed for each column? |
| `load_YAML_parameters` and `update_assimPot` NI branch | The NI effect on `txConversion` is duplicated and not sourced in the audit. | Proposed only as active-code documentation with warning. | What scientific meaning and calibration source should be attached to `NI`, `NIYo`, `NIp`, `LGauss`, `AGauss`? |
| `estimate_KAssim`, `estimate_conv`, `update_assimPot` | Beer-Lambert/PAR/RUE family is clear, but phase coefficients and conversion factor `10` are not externally validated. | Existing docstrings can remain factual; avoid stronger reference claims. | Is `PAR = 0.5 * rg` and `*10` conversion validated for all supported crops and units? |
| `calculate_maintainance_respiration` | Q10 response is clear, but biomass pool definition may double-count or include leaves in a way needing validation. | Keep current cautious docstring. | Should `biomasseTotale` include all organs for maintenance respiration in this implementation? |
| `update_potential_yield`, `update_potential_yield_delta`, `update_yield_during_filling_phase` | Yield coefficients and phase gates are central but not matched to a public exact source. | Existing cautious docstrings are preferable until formalism is reviewed. | Which SARRA-H/SARRA-O calibration document defines these yield equations? |
| `EvalFeuilleTigeSarrahV4`, `update_leaf_biomass`, `update_stem_biomass`, `calculate_canopy_specific_leaf_area`, `calculate_leaf_area_index` | Current docstrings describe active equations, but exact empirical provenance is still unclear. | No additional direct changes in this pass. | Are the phase-dependent partition and SLA equations crop-specific calibrations or generic SARRA defaults? |
| `estimate_critical_nitrogen_concentration` | Justes et al. (1994) uses a winter-wheat shoot biomass dilution curve, while SARRA-Py uses `4.8 * biomasseTotale**(-0.33)`. | Keep warning that Justes is only related, not exact. | Should the N dilution curve be crop-specific and based on aboveground biomass rather than total biomass? |
| `BiomDensOptSarraV4`, `BiomDensiteSarraV42`, `BiomMcUBTSV3`, `MAJBiomMcSV3` | Legacy or apparently unused functions; scientific status unclear. | Do not spend docstring budget until public/legacy status is decided. | Are these functions still part of supported notebook workflows? |

## Proposed Snippets For Later Review

### `update_root_tank_stock`

```python
"""Update the water stock considered accessible to roots.

Scientific formulation
----------------------
The current implementation propagates `root_tank_stock` from day `j` onward.
When the root reservoir is deeper than the surface reservoir, it adds
`delta_root_tank_capacity`; otherwise it estimates accessible stock from the
surface reservoir filling ratio after subtracting 10% bound water.

Notes
-----
This docstring describes the active code only. The operation mixes a capacity
increment and a water stock increment, and should be reviewed with a water
mass-balance test before any scientific validation claim is added.
"""
```

### `estimate_runoff`

```python
"""Estimate daily runoff from a threshold and runoff fraction.

Scientific formulation
----------------------
The current implementation triggers runoff when `rain > runoff_threshold`, then
computes `runoff = (available_water - runoff_threshold) * runoff_rate`.

Notes
-----
`available_water` may already include irrigation and mulch interception effects,
while the trigger uses rainfall only. This rule is documented as active code
and still needs hydrological validation.
"""
```

### `load_iSDA_soil_data_alternate`

```python
"""Load local soil rasters and derive SARRA-Py soil variables.

The helper reprojects local Africa soil-grid assets to the rainfall grid,
creates soil texture classes, maps selected classes through a project CSV table,
converts runoff rate from percent to fraction, and derives `ru` from RZPAWC and
root-zone depth.

Notes
-----
The external datasets are documented, but the adapted rasters and local
correspondence table are project assets. Their provenance and units should be
confirmed before adding stronger scientific claims.
"""
```

### `load_YAML_parameters`

```python
"""Load variety, management and soil YAML parameters.

The helper reads project-relative YAML files, converts the sowing date to a
`datetime.date`, and optionally recomputes `txConversion` when `NI` is defined.

Notes
-----
The `NI` response is active code but is not sourced in the current audit. The
formula should be validated before being documented as a scientific formalism.
"""
```
