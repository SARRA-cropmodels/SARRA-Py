# Scientific Validation Questions

Date: 2026-06-04

This file collects scientific or numerical points that should be validated
before changing equations, strengthening docstrings, or making larger refactors.
No calculation was changed during this pass.

## High Priority

| Topic | Current code behaviour | Risk | Validation question |
|---|---|---|---|
| Thermal time formula | `ddj` is computed from `tpMoy` with thresholds `TBase`, `TOpt1`, `TOpt2`, `TLim`; older comments mention a Tmin/Tmax method. | Changes phenology, phase durations, biomass and yield. | Is the active `tpMoy` formulation scientifically intended for SARRA-Py? |
| Root stock update | `update_root_tank_stock` can add `delta_root_tank_capacity` directly to `root_tank_stock`. | Potential water creation or mass-balance inconsistency. | Does the capacity increment represent newly accessible water already present in the soil, or should stock and capacity be separated differently? |
| Plant transpiration cap | `update_plant_transpiration` transforms excessive transpiration with `max(root_tank_stock - tr, 0)`. | Could under-consume or zero transpiration unexpectedly. | Should this be `min(tr, root_tank_stock)` or is the residual formula intentional? |
| Runoff trigger | Runoff is triggered by `rain > runoff_threshold` but computed from `available_water`, which may include irrigation and exclude mulch capture. | Silent inconsistency for irrigated or mulched scenarios. | Which water amount should trigger runoff in SARRA-Py? |
| `engine="numpy"` default | Public default remains `engine="xarray"`; NumPy engine is optional. | API/scientific trust risk if changed too early. | When realistic notebook benchmarks and reduced tests are sufficient, should NumPy become default? |

## Hydrology And Soil

| Topic | Current code behaviour | Risk | Validation question |
|---|---|---|---|
| FESW denominator | Active code uses `surface_tank_capacity`; old comments mention 110%. | Documentation drift and possible calibration mismatch. | Is 100% capacity the validated denominator? |
| Surface tank cap | `update_surface_tank_stock` comments mention 110%, but active code caps at 100%. | Same as above; affects evaporation. | Was the 110% cap intentionally removed? |
| Mulch interception units | `water_captured_by_mulch` uses `/1000` for `surfMc` and `/10000` for kg/ha to mm conversions. | Unit errors may be small but systematic. | Are `surfMc`, `coefMc`, `humSatMc` and `biomMc` units documented and calibrated? |
| Mulch evaporation denominator | `FEMcW = mulch_water_stock / (humSatMc * biomMc / 1000)` can divide by zero when `biomMc == 0`. | Known warnings; possible NaN propagation. | Should zero mulch biomass force `FEMcW = 0`? |
| Soil loader provenance | iSDA/Africa soil-grid sources are identifiable, but local adapted rasters and CSV tables drive model parameters. | Reproducibility and unit ambiguity. | Which local assets are authoritative, and should metadata record their source/version? |
| Root-zone water capacity | `ru = RZPAWC / (profRu/1000)` after `profRu` conversion from cm to mm. | Unit mismatch if source files change. | Are `RZPAWC` and `profRu` units guaranteed in all notebook assets? |
| Humectation front reset | End-of-season functions reset or store humectation/front stocks for possible second cycles. | Multi-cycle workflows could behave unexpectedly. | Are multiple crop cycles within one simulation still supported and validated? |

## Carbon, Nitrogen And Yield

| Topic | Current code behaviour | Risk | Validation question |
|---|---|---|---|
| PAR fraction | `update_assimPot` uses `PAR = 0.5 * rg`. | Common assumption, but affects absolute biomass. | Is 0.5 retained for all supported meteorological sources and crops? |
| Intercepted PAR and conversion | `assimPot = PAR * (1 - exp(-kdf*lai)) * conv * 10`. | `*10` and `conv` units are not self-evident. | What exact unit conversion and calibration justify the factor 10? |
| NI conversion formula | `txConversion` is recomputed from `NI` with exponential and Gaussian terms in two places. | Duplicate unsourced formula, mutation of `paramVariete`. | What does `NI` represent scientifically and where is the formula calibrated? |
| KAssim interpolation | Phase 5 and 6 conversion coefficients interpolate by thermal time thresholds. | Division by zero if thresholds coincide; phase response can dominate biomass. | Are threshold differences guaranteed positive? |
| Maintenance respiration | `respMaint = kRespMaint * biomasseTotale * 2**((tpMoy-tempMaint)/10)`. | Pool definition may double-count organs or include reserve biomass. | Should respiration use total, aboveground, vegetative, or organ-specific biomass? |
| Biomass partition | Leaf/stem/root partition uses phase-dependent empirical coefficients. | Yield and LAI sensitive to coefficients. | Are these generic SARRA equations or crop/variety-specific calibrations? |
| SLA and LAI | SLA is computed from biomass and phenological progress, then `lai` from leaf biomass and SLA. | Division warnings and units can affect light interception. | Are zero-biomass and very low-biomass cases supposed to return zero, NaN, or previous state? |
| Potential yield | Yield potential and daily demand use phase-specific biomass and thresholds. | Central agronomic output; no exact public source matched. | Which SARRA-H/SARRA-O reference defines the active yield formalism? |
| Critical nitrogen dilution | Active code uses `4.8 * biomasseTotale**(-0.33)`; Justes et al. (1994) is related but not exact. | Possible crop mismatch and total-vs-shoot biomass mismatch. | Should the equation be crop-specific and based on shoot/aboveground biomass? |

## Data Preparation And Coordinates

| Topic | Current code behaviour | Risk | Validation question |
|---|---|---|---|
| Day length longitude | `calc_day_length` fixes longitude to 0.0 and uses latitude/date. | Day length is mostly latitude-driven, but civil sunrise/sunset intervals can depend on location/timezone handling. | Is longitude 0 acceptable for all day-length use in SARRA-Py? |
| Day length coordinate | `calc_day_length_raster_fast` assumes `data["y"]` is latitude. | Wrong if grid dimensions or CRS are not standard lat/lon. | Should the helper validate CRS and latitude axis before computing day length? |
| AgERA5 radiation units | Loaders divide `rg` by 1000, assuming local files are kJ m-2 day-1. | Official AgERA5 documentation commonly states J m-2 day-1; local preprocessing may differ. | Are the project AgERA5 files guaranteed to be kJ m-2 day-1? |
| TAMSAT variable choice | Fast loader stores `band_data`; TAMSAT NetCDF products expose variables such as `rfe` and `rfe_filled`. | Loader is tied to local converted rasters or rasterized NetCDF output. | Should loaders document accepted file schema and variable names? |
| YAML relative paths | Parameter loaders use `../data/params/...` relative paths. | Notebook working directory dependency. | Should loaders accept absolute paths while preserving backward compatibility? |

## Documentation Policy Questions

- Should code docstrings cite only sources that match the exact equation, or may
  they cite family-level sources using "related to" wording?
- Should legacy functions be documented as supported public API, or moved to a
  legacy review section after import-stability tests are expanded?
- Should formalism documentation live primarily in docstrings, or should
  docstrings stay short and link to a maintained scientific reference document?
