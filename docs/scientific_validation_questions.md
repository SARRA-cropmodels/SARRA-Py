# Scientific Validation Questions

Date: 2026-06-04

This file lists scientific, numerical and provenance questions that should be
answered before changing equations, strengthening source claims or refactoring
model internals. No calculation is changed by this documentation pass.

## High Priority

| Topic | Current code behaviour | Risk | Validation question |
|---|---|---|---|
| Thermal time formula | `ddj` is computed from `tpMoy` with thresholds `TBase`, `TOpt1`, `TOpt2`, `TLim`; older comments mention a Tmin/Tmax method. | Changes phenology, phase durations, biomass and yield. | Is the active `tpMoy` formulation the validated SARRA-Py thermal-time formalism? |
| Root stock update | `update_root_tank_stock` can add `delta_root_tank_capacity` directly to `root_tank_stock`. | Potential water creation or mass-balance inconsistency. | Does the capacity increment represent newly accessible stored water, or should stock and capacity be separated differently? |
| Plant transpiration cap | `update_plant_transpiration` transforms excessive transpiration with `max(root_tank_stock - tr, 0)`. | Could under-consume or zero transpiration unexpectedly. | Should transpiration be capped by available root stock, or is the current residual expression intentional? |
| Runoff trigger | Runoff is triggered by `rain > runoff_threshold` but computed from `available_water`, which may include irrigation and exclude mulch capture. | Silent inconsistency for irrigated or mulched scenarios. | Should runoff be triggered by rainfall only, or by post-mulch/post-irrigation available water? |
| Source-status policy | Some formalisms are only family-level matches to FAO-56, SARRA-H, Impatience, Justes or RUE literature. | Overclaiming could mislead users about scientific validation. | Which external sources are accepted as exact validation sources, and which should remain "Source-related"? |

## Hydrology And Soil

| Topic | Current code behaviour | Risk | Validation question |
|---|---|---|---|
| FESW denominator | Active code uses `surface_tank_capacity`; old comments mention 110%. | Documentation drift and possible calibration mismatch. | Is 100% capacity the validated denominator? |
| Surface tank cap | `update_surface_tank_stock` comments mention 110%, but active code caps at 100%. | Affects surface storage and evaporation. | Was the 110% cap intentionally removed? |
| Validate the squared FESW soil evaporation response | `evap = min(evapPot * fesw**2, surface_tank_stock)`. This can be interpreted as a Noah-like power-law soil evaporative efficiency function with exponent `n = 2`. | No direct SARRA-independent validation has been established for `n = 2`; it may compensate for surface-reservoir thickness or may suppress soil evaporation too strongly. | Run sensitivity tests with `n = 1`, `1.5`, `2` and `3` under bare-soil and cropped scenarios. Compare cumulative soil evaporation, transpiration, surface stock, root-zone stock, water-stress days, biomass and yield. |
| Future soil evaporation exponent parameter | The exponent is hard-coded as `fesw**2`. A future documentation/API candidate would be `soil_evap_stress_exponent = 2`, but it is not active code. | Exposing it too early could imply calibration support that does not yet exist. | Keep it as a validation-study note until sensitivity tests justify whether it should become a named parameter. |
| Validate crop-residue mulch interception and unit conversions | `water_captured_by_mulch = min(available_water * (1 - exp(-surfMc / 1000 * biomMc)), humSatMc * biomMc / 10000 - mulch_water_stock)`. This is strongly related to empirical crop-residue mulch formalisms such as Scopel et al. (2004), especially exponential residue cover and storage-limited interception. | Unit errors or input-water interpretation errors may systematically affect infiltration, runoff, evaporation, transpiration, biomass and yield. | Confirm units of `biomMc`, `surfMc`, `humSatMc`, `mulch_water_stock`; confirm `/1000` and `/10000`; confirm whether `available_water` rather than rainfall alone is intended; test irrigation-only, rainfall-only and mixed scenarios; test dry versus saturated initial mulch; check whether captured water can become negative when mulch stock exceeds nominal storage; compare cumulative intercepted water, mulch evaporation, soil evaporation, runoff, transpiration, drainage, biomass and yield across `biomMc = 0`, low, medium and high. |
| Validate mulch effect on runoff | Mulch reduces runoff indirectly because `compute_runoff` runs after `fill_mulch`, so runoff uses post-mulch `available_water`; however, the trigger remains `rain > runoff_threshold`. | Scopel et al. highlight runoff reduction as a main residue effect, and runoff behaviour can dominate yield predictions in dry scenarios. | Should runoff be triggered by rainfall only, or by post-mulch available water? Does the current order match the intended hydrological logic for rainfed, irrigated and mixed events? |
| Mulch evaporation denominator | `FEMcW = mulch_water_stock / (humSatMc * biomMc / 1000)` can divide by zero when `biomMc == 0`. | Known warnings; possible NaN propagation. | Should zero mulch biomass force `FEMcW = 0`? |
| Soil loader provenance | iSDA/Africa soil-grid sources are identifiable, but local adapted rasters and CSV tables drive model parameters. | Reproducibility and unit ambiguity. | Which local assets are authoritative, and should metadata record their source/version? |
| Root-zone water capacity | `ru = RZPAWC / (profRu/1000)` after `profRu` conversion from cm to mm. | Unit mismatch if source files change. | Are `RZPAWC` and `profRu` units guaranteed in all notebook assets? |
| Humectation front reset | End-of-season functions reset or store humectation/front stocks for possible second cycles. | Multi-cycle workflows could behave unexpectedly. | Are multiple crop cycles within one simulation still supported and validated? |

## Carbon, Nitrogen And Yield

| Topic | Current code behaviour | Risk | Validation question |
|---|---|---|---|
| PAR fraction | `update_assimPot` uses `PAR = 0.5 * rg` after initialization. | Common assumption, but affects absolute biomass. | Is 0.5 retained for all supported meteorological sources and crops? |
| Conversion factor 10 | `assimPot = PAR * (1 - exp(-kdf*lai)) * conv * 10`. | Unit conversion and calibration are not self-evident. | What exact unit conversion and SARRA calibration justify the factor 10? |
| `assimPot` unit | Metadata says kg/ha, while the daily loop and equation imply a daily flux. | Output interpretation and documentation may be wrong. | Should `assimPot` and `assim` be documented as kg ha-1 day-1, kg ha-1 per step, or legacy kg/ha convention? |
| NI conversion formula | `txConversion` is recomputed from `NI` with exponential and Gaussian terms in two places. | Duplicate unsourced formula, mutation of `paramVariete`. | What does `NI` represent scientifically and where is the formula calibrated? |
| KAssim interpolation | Phase 5 and 6 conversion coefficients interpolate by thermal time thresholds. | Division by zero if thresholds coincide; phase response can dominate biomass. | Are threshold differences guaranteed positive? |
| Maintenance respiration | `respMaint` applies a Q10-like factor to total biomass plus leaf biomass. | Pool definition may double-count leaves or intentionally weight leaf respiration. | Should respiration use total, aboveground, vegetative, or organ-specific biomass? |
| Biomass partition | Leaf/stem/root partition uses phase-dependent empirical coefficients and floors. | Yield and LAI are sensitive to coefficients. | Are these generic SARRA equations or crop/variety-specific calibrations? |
| SLA and LAI warnings | SLA ratios divide by `biomasseFeuille[j]`; yield and assimilation divide by `trPot`; Ncrit uses a negative power of biomass. | Runtime warnings and potential NaN/inf values. | Should zero-biomass and zero-demand cases return zero, NaN, previous state, or a guarded diagnostic? |
| Potential yield | `rdtPot` uses `KRdtPotA`, `KRdtPotB`, `KRdtBiom` and a `2 * biomasseTige` cap. | Central agronomic output; no exact public source matched. | Which SARRA-H/SARRA-O reference defines the active potential-yield equation? |
| Daily grain filling demand | `dRdtPot` uses thermal time, transpiration ratio and `respMaint * 0.15` lower bound. | Central yield pathway with weak source traceability. | What is the scientific source and unit convention for the daily filling demand equation? |
| Ncrit equation | Active code uses `Ncrit = 5.35 * (biomasseTotale / 1000)**(-0.44)`. | Possible crop mismatch, total-vs-shoot biomass mismatch and infinite values at zero biomass. | Is this a Justes-type critical nitrogen curve, a SARRA calibration, or an internal diagnostic? |
| Ncrit unit | Code metadata leaves `Ncrit` units empty. | Users cannot interpret whether it is percent, g kg-1 or an index. | What unit should be assigned to `Ncrit`, and should it be exposed as a scientific output? |

## Phenology And Photoperiodism

| Topic | Current code behaviour | Risk | Validation question |
|---|---|---|---|
| Impatience equation | `update_photoperiodism` computes `sumPP` from day length, thermal time and parameters `PPExp`, `PPCrit`, `SeuilPP`, `PPsens`. | Source family known, exact equation not matched. | Does the active equation exactly match Dingkuhn et al. (2008) or another SARRA-H source? |
| Photoperiod reset | On phase-3 entry, `sumPP` is set to 100. | Phase transition timing may depend on this initialization. | Is the reset value 100 part of the validated formalism? |
| Phase-6 root growth | `update_root_growth_speed` has a mapping for phase 6 but loops over phases 1-5. | Root growth may stop earlier than intended. | Should phase 6 receive `VRacMatu2`, or is the current loop intentional? |
| Mortality equality trigger | Juvenile mortality uses `nbjStress == seuilCstrMortality`. | Equality may miss pixels that step over the threshold. | Should mortality trigger on equality only, or on `>=`? |

## Data Preparation And Coordinates

| Topic | Current code behaviour | Risk | Validation question |
|---|---|---|---|
| Day length longitude | `calc_day_length` fixes longitude to 0.0 and uses latitude/date. | Day length is mostly latitude-driven, but civil sunrise/sunset intervals can depend on location/timezone handling. | Is longitude 0 acceptable for all day-length use in SARRA-Py? |
| Day length coordinate | `calc_day_length_raster_fast` assumes `data["y"]` is latitude. | Wrong if grid dimensions or CRS are not standard lat/lon. | Should the helper validate CRS and latitude axis before computing day length? |
| AgERA5 radiation units | Loaders divide `rg` by 1000, assuming local files should become MJ m-2 day-1. | Official/raw product units and local preprocessing may differ. | Are the project AgERA5 files guaranteed to require this `/1000` conversion? |
| TAMSAT variable choice | Fast loader stores `band_data`; TAMSAT NetCDF products may expose named variables such as `rfe` or `rfe_filled`. | Loader is tied to local converted rasters or rasterized NetCDF output. | Should loaders document accepted file schema and variable names? |
| YAML relative paths | Parameter loaders use `../data/params/...` relative paths. | Notebook working directory dependency. | Should loaders accept absolute paths while preserving backward compatibility? |

## Bibliography TODOs

- Verify exact bibliographic details and equation relevance for Dingkuhn et al.
  2003, Baron et al. 2005, Kouressy et al. 2008, Lalou et al. 2019, Folliard et
  al. 2004, Scopel et al. 2004, Ranaivoson et al. 2017, Monteith 1977, Sinclair
  and Muchow 1999, and Justes et al. 1994 before using them as exact sources.
- Identify which SARRA-H/SARRA-O documentation page, Pascal procedure or
  calibration note should be cited for yield, biomass partition, mulch and root
  reservoir equations.
