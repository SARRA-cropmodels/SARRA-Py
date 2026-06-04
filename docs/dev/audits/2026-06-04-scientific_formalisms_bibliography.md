# Scientific Formalisms Bibliography

Date: 2026-06-04

This document records the bibliography pass used for the docstring v2 audit.
It distinguishes observed code, external sources, and interpretation. A source
can confirm an equation, confirm only the model family, or fail to match the
current implementation closely enough for a direct code docstring.

## Source Matching Scale

- **exact**: the active equation matches the cited source at the level needed for
  a docstring.
- **close**: the active equation is an algebraic or variable-convention variant
  of the source.
- **family only**: the source supports the modelling family, but not the exact
  SARRA-Py equation.
- **not found**: no reliable matching source was found in this pass.

## Bibliography Map

| Formalism | Functions concerned | Active code or calculation summary | Sources consulted | Source retained | Source/code match | Confidence |
|---|---|---|---|---|---|---|
| SARRA-Py daily spatial crop model | `run_model`, `run_waterbalance_model`, scientific wrappers | Daily loop over phenology, hydrology, carbon balance and yield on a georeferenced xarray grid. | SARRA-Py documentation; CIRAD SARRA-O page. | https://sarra-cropmodels.github.io/SARRA-Py/ and https://www.cirad.fr/en/cirad-news/news/2019/science/sarra-o-model | family only | high |
| Public notebook execution engines | `models._run_with_engine`, `run_model`, `run_waterbalance_model` | `engine="xarray"` keeps legacy xarray state; `engine="numpy"` converts internal state to NumPy arrays and restores xarray outputs. | Code inspection only. | none | exact to code | high |
| Day length from sunrise/sunset | `calc_day_length`, `_cached_day_length_matrix`, `calc_day_length_raster_fast` | Astral `sun.daylight(observer, date)` gives sunrise/sunset interval; SARRA-Py returns hours and broadcasts by latitude. | Astral documentation. | https://astral.readthedocs.io/en/stable/index.html | close | high |
| TAMSAT rainfall loading | `build_rainfall_files_df`, `load_TAMSAT_data`, `load_TAMSAT_data_fast` | Local date-coded rasters are concatenated into `data["rain"]`; rainfall is treated as daily mm. | TAMSAT University of Reading page; Maidment et al. (2017), Scientific Data. | https://research.reading.ac.uk/tamsat/rainfall/ and https://www.nature.com/articles/sdata201763 | close for dataset, not file naming | high |
| AgERA5 forcing loading and radiation units | `load_AgERA5_data`, `load_AgERA5_data_fast_dask` | Selected folders are mapped to `tpMoy`, `ET0`, `rg`; `rg` is divided by 1000 in local files. | AgERA5/Copernicus documentation. | https://docs.answr.space/data-sources/agera5 | close for source units; local kJ-to-MJ assumption remains project-specific | medium |
| iSDA/Africa soil grids and root-zone properties | `load_iSDA_soil_data`, `load_iSDA_soil_data_alternate` | Soil texture class, root-zone depth, RZPAWC and runoff table values are reprojected to the rainfall grid; soil classes map through local CSV tables. | iSDA API; iSDAsoil and Africa soil-property papers; Leenaars et al. (2018). | https://api.isda-africa.com/isdasoil/v2/docs, https://www.nature.com/articles/s41598-021-85639-y, https://pmc.ncbi.nlm.nih.gov/articles/PMC5913732/ | family only for local tables | medium |
| Thermal time response to mean temperature | `calculate_daily_thermal_time`, `calculate_once_daily_thermal_time` | Piecewise response based on `tpMoy`, `TBase`, `TOpt1`, `TOpt2`, `TLim`; older Tmin/Tmax comment is not active. | Existing audit; crop degree-day literature not mapped exactly in this pass. | none | not found | low |
| Phenological phase transitions | `EvalPhenoSarrahV3`, `update_pheno_phase_*`, `flag_change_phase` | Phase changes occur when accumulated thermal time reaches variety thresholds; state is propagated from `j` onward. | SARRA-Py docs; SARRA-O/CIRAD context; original Pascal comments in code. | SARRA family documentation only. | family only | medium |
| Sorghum photoperiodism / impatience | `update_photoperiodism` | Uses day length above `PPCrit`, `SeuilPP`, `PPExp`, `PPsens` and thermal time since previous phase to keep or end phase 3. | Dingkuhn et al. (2008), CIRAD notice; related sorghum photoperiodism papers. | https://publications.cirad.fr/une_notice.php?dk=543204 | family only | medium |
| Surface evaporable water fraction | `estimate_fesw` | `fesw = surface_tank_stock / surface_tank_capacity`. | FAO-56; Alhassane thesis URL present in code comments. | FAO-56 for related soil-water availability concepts. | family only | medium |
| Soil evaporation coefficient and mulch cover | `estimate_kce`, `estimate_soil_potential_evaporation`, `estimate_soil_evaporation` | `kce = ltr * mulch * exp(-coefMc * surfMc * biomMc / 1000)`; `evapPot = ET0*kce`; `evap = min(evapPot*fesw**2, surface_stock)`. | FAO-56 dual crop coefficient chapter; code comments referencing SARRA/Pascal and Alhassane. | FAO-56 only as related family. | family only | medium-low |
| FTSW, p factor and water-stress coefficient | `estimate_ftsw`, `estimate_pFact`, `estimate_cstr`, `estimate_plant_transpiration` | `ftsw = stock/capacity`; `pFact = clip(PFactor + 0.04*(5-kcp*ET0), 0.1, 0.8)`; `cstr = clip(ftsw/(1-pFact), 0, 1)`; `tr=trPot*cstr`. | FAO-56 chapter 8. | https://www.fao.org/4/x0490e/x0490e0e.htm | close for `p` and `Ks` family; reservoir convention differs | high for docstring wording, medium for scientific validation |
| Root reservoir growth and humectation front | `EvolRurCstr2`, `initialize_delta_root_tank_capacity`, `update_root_tank_stock`, `fill_tanks` | Root capacity grows with `vRac`, `ru`, stress modifier `min(cstr+0.3,1)`, and humectation-front bounds; stock updates mix capacity and water stock. | SARRA-Py docs; original comments. | none for exact equation | not found | low |
| Runoff threshold and rate | `estimate_runoff`, `compute_runoff` | If `rain > runoff_threshold`, runoff is `(available_water - threshold) * runoff_rate`. | Soil table provenance in project files; no hydrology source matched. | none | not found | low |
| Mulch water interception and evaporation | `compute_water_captured_by_mulch`, `estimate_FEMcW_and_update_mulch_water_stock` | Exponential cover from mulch biomass; conversions between kg/ha and mm water; FEMcW squared evaporation response. | Code comments cite Scopel/Maceina; no source verified in this pass. | none | not found | low |
| Beer-Lambert canopy light interception and RUE-like assimilation | `estimate_ltr`, `update_assimPot`, `update_assim`, `estimate_KAssim`, `estimate_conv` | `ltr=exp(-kdf*lai)`; PAR is `0.5*rg`; intercepted PAR is scaled by conversion coefficients and `*10`; assimilation is scaled by `tr/trPot`. | Monteith/RUE references; general crop modelling references; SARRA docs. | Monteith (1977) and general Beer-Lambert/RUE literature as family only. | family only | medium |
| Q10 maintenance respiration | `calculate_maintainance_respiration` | `respMaint = kRespMaint * biomasseTotale * 2**((tpMoy-tempMaint)/10)`. | General plant respiration/Q10 model references; no SARRA-specific source matched. | none in code | family only | medium-low |
| Biomass partition, SLA and LAI | `EvalFeuilleTigeSarrahV4`, `update_leaf_biomass`, `update_stem_biomass`, `calculate_canopy_specific_leaf_area`, `calculate_leaf_area_index` | Empirical phase-dependent partitioning, SLA interpolation with biomass and phenology, `lai = SLA * leaf biomass / 10000`. | General LAI/SLA concepts; no exact SARRA equation source matched. | none for exact equations | family only | low-medium |
| Yield potential and filling | `update_potential_yield`, `update_potential_yield_delta`, `update_yield_during_filling_phase` | Potential yield and daily filling demand are driven by biomass and phase thresholds; current code caps/floors through local conditions. | SARRA family documentation only. | none for exact equations | not found | low |
| Critical nitrogen dilution curve | `estimate_critical_nitrogen_concentration` | `critical_nitrogen_concentration = 4.8 * biomasseTotale**(-0.33)` in the active code. | Justes et al. (1994); critical nitrogen dilution literature. | DOI: 10.1006/anbo.1994.1133 | family only: coefficient/exponent and biomass basis differ from Justes wheat shoot curve | medium-low |
| YAML parameter loading and NI conversion | `load_paramVariete`, `load_paramITK`, `load_paramTypeSol`, `load_YAML_parameters`, `update_assimPot` | Loads project-relative YAML files; converts sowing date; recomputes `txConversion` from `NI` using exponential/Gaussian terms. | Code inspection only. | none | exact to code, no source | low |

## Sources Retained For Code Docstrings In This Pass

- Allen et al. (1998), FAO Irrigation and Drainage Paper 56: retained only for
  FAO-like `p`, `Ks`, crop-coefficient and soil-water availability wording.
- Astral documentation: retained for `calc_day_length`.
- TAMSAT University of Reading and Maidment et al. (2017): retained for loader
  context, not for local file naming.
- AgERA5 documentation: retained for dataset variable/unit context, with local
  unit-conversion caveat.

## Sources Kept Out Of Code Docstrings

- Dingkuhn et al. (2008): relevant to photoperiodism, but the exact SARRA-Py
  equation still needs domain validation.
- Justes et al. (1994): relevant to critical N dilution, but the SARRA-Py
  coefficient/exponent and biomass basis do not match exactly.
- Monteith/RUE and Beer-Lambert general sources: useful family references, but
  not enough to validate SARRA-Py conversion factors and phase coefficients.
- Soil/iSDA sources: validate datasets, not the local texture-to-parameter CSV
  nor runoff table choices.
