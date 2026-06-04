# SARRA-Py Model Formalisms

## Scope And Status

This document describes the active scientific and technical formalisms observed
in the current SARRA-Py code. It is a maintained model overview, not a complete
agronomic validation report. Raw audit notes are archived under
`docs/dev/audits/`.

SARRA-Py is a daily spatial crop model run from notebook workflows on xarray
inputs and outputs. The public default remains `engine="xarray"`;
`engine="numpy"` is an internal execution option intended to preserve the same
scientific behaviour and xarray-facing outputs.

## Validation Status Legend

| Status | Meaning |
|---|---|
| Code-observed | The equation or behaviour is directly observed in active SARRA-Py code. No exact source match is claimed. |
| Source-related | The equation belongs to, or is consistent with, a known modelling family, but differs in variables, units, reservoirs, timing or implementation details. |
| Validated | The equation, variables, units and behaviour have been checked against a source and examples/tests. This status is not used for any full SARRA-Py formalism in this document yet. |
| Open validation point | The active code is documented, but a scientific or numerical question must be answered before stronger wording or refactoring. |

## State And Time Step

Implemented in: `sarra_py/models.py::run_model`,
`sarra_py/models.py::_run_loop`.

Dynamic variables are simulated on a daily time axis and a spatial grid. Most
scientific functions mutate the model state in place and often propagate the
current value from day `j` to the end of the simulation with `j:`.

State convention used in this document:

- `X_j_before`: value available at the start of day `j`.
- `X_j_after`: value after the current process on day `j`.
- `X_{j+1}`: value available to the next daily step.

The process order inside the daily loop is part of the numerical definition:

1. Phenology and accumulated thermal time.
2. Irrigation, rainfall input, mulch interception, runoff and reservoir filling.
3. Soil evaporation, transpiration and water consumption.
4. Carbon assimilation, biomass partitioning, LAI and yield.
5. Photoperiodism, mortality and nitrogen indicator.

Status: **Code-observed**.

## Variable And Unit Table

Units are taken from dataset attributes, code comments and active calculations.
When a unit is uncertain, the table marks it as an open validation point instead
of guessing.

| Variable | Meaning | Unit/status | Main functions |
|---|---|---|---|
| `tpMoy` | Mean daily temperature | deg C | `calculate_daily_thermal_time`, `update_assimPot`, `calculate_maintainance_respiration` |
| `ET0` | Reference evapotranspiration | mm day-1 | `estimate_soil_potential_evaporation`, `estimate_potential_plant_transpiration` |
| `rg` | Global radiation | MJ m-2 day-1 after loader conversion | `load_AgERA5_data*`, `initialize_simulation` |
| `rain` | Rainfall | mm day-1 | `load_TAMSAT_data*`, `compute_total_available_water` |
| `irrigTotDay` | Daily irrigation total | mm day-1 | `compute_daily_irrigation`, `compute_total_available_water` |
| `ddj` | Daily thermal time | degree-days day-1 | `calculate_daily_thermal_time`, `calculate_once_daily_thermal_time` |
| `sdj` | Accumulated thermal time | degree-days | `calculate_sum_of_thermal_time`, `EvalPhenoSarrahV3` |
| `dureeDuJour` | Daylight duration | hours | `calc_day_length_raster_fast`, `update_photoperiodism` |
| `lai` | Leaf area index | m2 m-2 | `calculate_leaf_area_index`, `estimate_ltr` |
| `ltr` | Non-intercepted light fraction | unitless | `estimate_ltr`, `estimate_kce` |
| `kcp` | Crop transpiration coefficient | unitless | `estimate_kcp`, `estimate_potential_plant_transpiration` |
| `kce` | Soil evaporation coefficient | unitless | `estimate_kce`, `estimate_soil_potential_evaporation` |
| `fesw` | Surface evaporable water fraction | unitless | `estimate_fesw`, `estimate_soil_evaporation` |
| `ftsw` | Root reservoir filling fraction | unitless | `estimate_ftsw`, `estimate_cstr` |
| `pFact` | Depletion fraction threshold | unitless | `estimate_pFact`, `estimate_cstr` |
| `cstr` | Water-stress coefficient | unitless | `estimate_cstr`, `estimate_plant_transpiration` |
| `trPot` | Potential plant transpiration | mm day-1 | `estimate_potential_plant_transpiration` |
| `tr` | Actual plant transpiration | mm day-1 | `estimate_plant_transpiration`, `ConsoResSep` |
| `evapPot` | Potential soil evaporation | mm day-1 | `estimate_soil_potential_evaporation` |
| `evap` | Actual soil evaporation demand | mm day-1 | `estimate_soil_evaporation`, `ConsoResSep` |
| `biomasseTotale` | Total crop biomass | kg ha-1 in variable metadata | `update_total_biomass`, `estimate_critical_nitrogen_concentration` |
| `assimPot` | Potential assimilation | metadata says kg ha-1; daily flux implied by equation | `update_assimPot` |
| `assim` | Actual assimilation | metadata says kg ha-1; daily flux implied by equation | `update_assim` |
| `rdt` | Grain yield | kg ha-1 | `update_yield_during_filling_phase` |
| `Ncrit` | Critical nitrogen indicator | open: likely percent or internal index; not set in metadata | `estimate_critical_nitrogen_concentration` |

## Phenology

Implemented in: `sarra_py/bilan_pheno.py::EvalPhenoSarrahV3`,
`calculate_daily_thermal_time`, `calculate_once_daily_thermal_time`,
`calculate_sum_of_thermal_time`, `update_photoperiodism`,
`MortaliteSarraV3`.

The crop cycle uses phases `0` to `7`: no crop, initialization/germination,
vegetative development, photoperiod-sensitive phase, reproductive phase,
filling/maturation steps and harvest.

Thermal transitions mainly compare accumulated thermal time `sdj` with variety
thresholds `SDJLevee`, `SDJBVP`, `SDJRPR`, `SDJMatu1` and `SDJMatu2`.

Active daily thermal-time equation using mean temperature `T = tpMoy`:

```text
if T <= TOpt2:
    ddj = max(min(TOpt1, T), TBase) - TBase
else:
    ddj = (TOpt1 - TBase)
          * (1 - ((min(TLim, T) - TOpt2) / (TLim - TOpt2)))
```

Temperatures are in degrees C and `ddj` is in degree-days day-1.

Status: **Code-observed** for the active `tpMoy` equation.

Open validation point: older comments mention a Tmin/Tmax formulation. The
active mean-temperature equation should not be described as scientifically
validated until that choice is confirmed.

## Photoperiodism

Implemented in: `sarra_py/data_preparation.py::calc_day_length_raster_fast`,
`sarra_py/bilan_pheno.py::update_photoperiodism`.

Day length is computed from date and latitude, then broadcast to the rainfall
grid. During phase 3, the active code computes:

```text
thermal_time_since_previous_phase = max(0.01, sdj - seuilTempPhasePrec)
time_above_critical_day_length = max(0, dureeDuJour - PPCrit)
sumPP = 100  # on phase-3 entry
sumPP = (1000 / thermal_time_since_previous_phase) ** PPExp
        * time_above_critical_day_length / (SeuilPP - PPCrit)
phasePhotoper = 0 if numPhase == 3 and sumPP < PPsens
```

Status: **Source-related**. This is related to the sorghum "Impatience" model
family, but this document does not claim exact implementation of Dingkuhn et
al. (2008) until the code equation and thresholds are matched to the source.

Open validation point: confirm `PPExp`, `PPsens`, `PPCrit`, `SeuilPP`, the reset
to 100 and the exact phase timing.

## Water Balance

Implemented in: `sarra_py/bilan_hydro.py::fill_tanks`,
`compute_total_available_water`, `compute_runoff`, `compute_soil_evaporation`,
`compute_transpiration`, `ConsoResSep`.

The conceptual balance is:

```text
stock(d+1) = stock(d) + inputs - runoff - drainage - evaporation - transpiration
```

The active code uses overlapping reservoirs, so this is not a one-to-one
identity for a single variable.

Reservoir table:

| Reservoir | Stock variable | Capacity variable | Unit | Inflows | Outflows/bounds | Main update functions |
|---|---|---|---|---|---|---|
| Surface reservoir | `surface_tank_stock` | `surface_tank_capacity` | mm | `available_water` after mulch/runoff | soil evaporation, shallow-root transpiration; capped at capacity | `update_surface_tank_stock`, `subtract_evap_from_surface_tank_stock`, `subtract_transpiration_from_surface_tank_stock_according_to_root_tank_stock` |
| Total/deep reservoir | `total_tank_stock` | `total_tank_capacity` | mm | `eauTranspi`, second-cycle carry-over | drainage, evaporation, transpiration | `update_total_tank_stock`, `compute_drainage`, `subtract_*_from_total_tank_stock` |
| Root-accessible reservoir | `root_tank_stock` | `root_tank_capacity` | mm | root growth and reservoir filling rules | transpiration and evaporation adjustments | `EvolRurCstr2`, `update_root_tank_stock`, `update_root_tank_stock_step_2` |
| Humectation front | `humectation_front` | bounded by `total_tank_capacity` | mm equivalent | reservoir filling / carry-over rules | bounds root growth capacity | `apply_humectation_front_boundaries`, end-of-season helpers |

Status: **Code-observed** for the reservoir mechanics. The reservoir approach is
**Source-related** to SARRA-H/SARRA family water-balance formalisms.

## Soil Evaporation

Implemented in: `sarra_py/bilan_hydro.py::estimate_fesw`,
`estimate_kce`, `estimate_soil_potential_evaporation`,
`estimate_soil_evaporation`, `compute_soil_evaporation`.

```text
fesw = surface_tank_stock / surface_tank_capacity
kce = ltr * mulch * exp(-coefMc * surfMc * biomMc / 1000)
evapPot = ET0 * kce
evap = min(evapPot * fesw**2, surface_tank_stock)
```

Units: `ET0`, `evapPot`, `evap`, `surface_tank_stock` and
`surface_tank_capacity` are millimetres for the daily step; `kce` and `fesw`
are unitless. `estimate_fesw`, `estimate_kce` and
`estimate_soil_potential_evaporation` write day `j`; `estimate_soil_evaporation`
propagates `evap` from day `j` onward with `j:`.

### Nonlinear Evaporative Efficiency

The squared `fesw` response can be interpreted as a nonlinear soil evaporative
efficiency function:

```text
E_actual = min(E_potential * f(theta), available_surface_water)
f(theta) = water_availability_index**n
```

In SARRA-Py:

```text
water_availability_index = fesw
n = 2
```

This is similar in abstract form to power-law bare-soil evaporation reductions
used in land surface models such as Noah LSM, where direct soil evaporation is
scaled by normalized top-layer soil water raised to an empirical exponent. In
that modelling family, an exponent near 2 represents a quadratic decline of
bare-soil evaporation as the near-surface layer dries.

For SARRA-Py, this remains an interpretation of the active code rather than a
validated source match. It may be a simple way to represent dry-surface-layer
effects when the modelled surface reservoir is thicker or more averaged than
the physically evaporating top millimetres.

### Difference From FAO-56

FAO-56 supports the general concept that soil evaporation decreases as the
evaporation layer dries. However, the FAO-56 dual crop coefficient method
commonly expresses stage-2 evaporation reduction through a depletion-based `Kr`
term using variables such as `De`, `TEW` and `REW`. SARRA-Py does not track
those FAO-56 variables in this equation.

Status: **Code-observed** for the active `fesw**2` equation; **Source-related,
not validated** for the Noah-like power-law interpretation; **Source-related**
only at family level for FAO-56 evaporation reduction concepts. Do not document
this equation as an exact Noah LSM, FAO-56 or SARRA-H implementation.

Open validation points: exponent `n = 2`, mulch coefficients/units, and
division by zero when capacities or mulch biomass are zero.

## Transpiration And Water Stress

Implemented in: `sarra_py/bilan_hydro.py::estimate_ftsw`,
`estimate_pFact`, `estimate_cstr`, `estimate_potential_plant_transpiration`,
`estimate_plant_transpiration`.

```text
ftsw = root_tank_stock / root_tank_capacity
pFact = PFactor + 0.04 * (5 - kcp * ET0)
pFact = clip(pFact, 0.1, 0.8)
cstr = clip(ftsw / (1 - pFact), 0, 1)
trPot = kcp * ET0
tr = trPot * cstr
```

Status: **Source-related**. The p-factor adjustment is FAO-56-like, but
SARRA-Py uses reservoir filling (`ftsw`) rather than FAO root-zone depletion.
Do not describe this as an exact FAO-56 implementation.

## Root Reservoir And Humectation Front

Implemented in: `sarra_py/bilan_hydro.py::EvolRurCstr2`,
`initialize_delta_root_tank_capacity`, `update_delta_root_tank_capacity`,
`update_root_tank_capacity`, `update_root_tank_stock`.

```text
delta_root_tank_capacity = vRac / 1000 * ru
if root_tank_capacity > surface_tank_capacity:
    delta_root_tank_capacity *= min(cstr + 0.3, 1.0)
delta_root_tank_capacity =
    min(delta_root_tank_capacity, humectation_front - root_tank_capacity)
```

Status: **Source-related** to SARRA-H reservoir and humectation-front
formalisms at family level; exact stock/capacity updates are **Code-observed**.

Open validation point: `update_root_tank_stock` mixes stock and capacity terms,
including adding `delta_root_tank_capacity` to `root_tank_stock`.

## Runoff, Drainage And Crop-Residue Mulch

Implemented in: `sarra_py/bilan_hydro.py::estimate_runoff`,
`compute_runoff`, `compute_water_captured_by_mulch`,
`update_available_water_after_mulch_filling`, `update_mulch_water_stock`,
`fill_mulch`, `estimate_kce`, `estimate_FEMcW_and_update_mulch_water_stock`,
`compute_drainage`.

Runoff:

```text
if rain > runoff_threshold:
    runoff = (available_water - runoff_threshold) * runoff_rate
else:
    runoff = 0
```

Status: **Code-observed**. The trigger uses rainfall while the amount uses
`available_water`, which can include irrigation and post-mulch adjustments.

### Crop-Residue Mulch Formalism

The active mulch module represents three Scopel-style residue effects:
interception and storage of incoming water, reduction of soil evaporation by
cover/radiation interception, and indirect runoff reduction because runoff is
computed after mulch interception has reduced `available_water`.

```text
mulch_cover = 1 - exp(-surfMc / 1000 * biomMc)

water_captured_by_mulch =
    min(
        available_water * mulch_cover,
        humSatMc * biomMc / 10000 - mulch_water_stock
    )

kce = ltr * mulch * exp(-coefMc * surfMc * biomMc / 1000)
```

Units observed in code and metadata: `available_water`,
`water_captured_by_mulch` and `mulch_water_stock` are millimetres for the daily
step; `biomMc` metadata says kg ha-1; `kce` and `mulch` are unitless. The units
of `surfMc`, `coefMc` and `humSatMc`, and the `/1000` and `/10000` conversions,
should be verified against the parameter source.

| Concept | Scopel-style role | SARRA-Py variable or expression | Status | Notes |
|---|---|---|---|---|
| Surface residue biomass | Amount of residue mulch on the soil surface | `biomMc` | Code-observed | Metadata says kg ha-1. |
| Exponential residue cover | Converts residue biomass to cover/interception fraction | `1 - exp(-surfMc / 1000 * biomMc)` | Source-related | Strongly consistent with empirical residue-cover formalisms; coefficients need unit validation. |
| Incoming water intercepted by residue | Rainfall-oriented residue interception | `available_water * mulch_cover` | Source-related | SARRA-Py uses `available_water`, which may include rainfall plus irrigation. |
| Maximum residue water storage | Water-holding capacity of residues | `humSatMc * biomMc / 10000` | Source-related | `/10000` conversion should be verified. |
| Current residue water stock | Water stored in mulch | `mulch_water_stock` | Code-observed | Propagated from day `j` onward after filling/evaporation updates. |
| Captured water | Storage-limited intercepted water | `min(available_water * cover, max_storage - mulch_water_stock)` | Source-related | Can become negative if stock exceeds nominal storage; needs validation. |
| Mulch evaporation | Evaporation from residue water stock | `mulch_water_stock -= ltr * ET0 * FEMcW**2` | Source-related | `FEMcW` denominator can divide by zero when `biomMc == 0`. |
| Radiation / soil evaporation reduction | Residue cover reduces soil evaporation coefficient | `exp(-coefMc * surfMc * biomMc / 1000)` inside `kce` | Source-related | Combined with canopy `ltr` and static `mulch` factor. |
| Runoff reduction | Residues reduce runoff by intercepting incoming water first | runoff uses post-mulch `available_water` | Code-observed indirect effect | Runoff trigger still uses `rain > runoff_threshold`. |

Status: **Source-related, relatively high confidence**, for relationship with
the empirical crop-residue mulch module described by Scopel et al. (2004),
especially exponential residue cover, storage-limited interception and mulch
effects on evaporation/runoff. It is not documented as an exact Scopel/STICS
implementation because coefficients, unit conversions and update order have not
been fully matched.

Open validation point: Scopel et al. describe residue interception primarily
for rainfall, while SARRA-Py applies the interception term to `available_water`,
which may include irrigation. Validate irrigated and saturated-mulch scenarios
before strengthening the source claim.

## Carbon Balance

Implemented in: `sarra_py/bilan_carbo.py::estimate_ltr`,
`estimate_KAssim`, `estimate_conv`, `update_assimPot`, `update_assim`,
`calculate_maintainance_respiration`, `update_total_biomass`.

Light interception and potential assimilation:

```text
ltr = exp(-kdf * lai)
PAR = 0.5 * rg
assimPot = PAR * (1 - exp(-kdf * lai)) * conv * 10
```

Water stress on assimilation:

```text
assim = assimPot * tr / trPot  # when trPot > 0
assim = 0                      # when trPot <= 0
```

Maintenance respiration and total biomass:

```text
respMaint = kRespMaint * biomasseTotale * 2**((tpMoy - tempMaint) / 10)
biomasseTotale(d+1) = biomasseTotale(d) + assim - respMaint
```

Status: **Source-related** for Beer-Lambert interception and big-leaf /
radiation-use-efficiency crop modelling. The PAR fraction `0.5`, the conversion
factor `10`, phase-dependent `KAssim` and `NI` response are **Code-observed**
SARRA-Py details requiring calibration/source confirmation.

Open validation point: `assimPot` metadata says kg ha-1, while the equation and
daily loop imply a daily flux. Confirm whether to document kg ha-1 day-1 or the
historical SARRA unit convention.

## Biomass Partition, LAI And Yield

Implemented in: `sarra_py/bilan_carbo.py::update_aboveground_biomass`,
`update_root_biomass`, `EvalFeuilleTigeSarrahV4`,
`calculate_canopy_specific_leaf_area`, `calculate_leaf_area_index`,
`update_potential_yield`, `update_potential_yield_delta`,
`estimate_reallocation`, `update_yield_during_filling_phase`.

Aboveground biomass during phases 2-4:

```text
biomasseAerienne =
    min(0.9, aeroTotPente * biomasseTotale + aeroTotBase)
    * biomasseTotale
```

Root biomass:

```text
biomasseRacinaire = biomasseTotale - biomasseAerienne
```

Leaf/stem partitioning uses empirical phase-dependent rules, including:

```text
bM = feuilAeroBase - 0.1
cM = ((feuilAeroPente * 1000) / bM + 0.78) / 0.75
biomasseFeuille =
    (0.1 + bM * cM ** ((biomasseAerienne - rdt) / 1000))
    * (biomasseAerienne - rdt)
biomasseTige = biomasseAerienne - biomasseFeuille - rdt
```

SLA is updated from old/new leaf biomass ratios and clipped to
`[slaMin, slaMax]`. The active LAI updater uses:

```text
lai = biomasseFeuille * sla  # phases 2-6
lai = 0                      # phases <= 1 or > 6
```

Potential yield at phase-5 entry:

```text
delta = biomTotStadeFloraison - biomTotStadeIp
rdtPot = KRdtPotA * delta + KRdtPotB + KRdtBiom * biomTotStadeFloraison
```

Daily potential filling demand:

```text
dRdtPot = max(
    rdtPot * (ddj / SDJMatu1) * (tr / trPot),
    respMaint * 0.15
)  # where trPot > 0
```

Yield filling:

```text
rdt = rdt + min(dRdtPot, max(0, deltaBiomasseAerienne) + reallocation)
```

Status: **Code-observed**. These equations are SARRA-Py/SARRA-H related, but
this document does not claim a verified public equation match for potential
yield, daily filling demand or empirical leaf/stem coefficients.

Open validation points: empirical coefficients, zero-biomass divisions in SLA,
division by `trPot`, and scientific source for yield-demand equations.

## Nitrogen Indicator

Implemented in:
`sarra_py/bilan_carbo.py::estimate_critical_nitrogen_concentration`.

```text
Ncrit = 5.35 * (biomasseTotale / 1000)**(-0.44)
```

If `biomasseTotale` is kg ha-1, division by 1000 converts it to t ha-1. The
code does not assign units to `Ncrit`, and no downstream agronomic use was
identified in the current daily loop beyond storing the diagnostic value.

Status: **Source-related** only. The equation resembles critical nitrogen
dilution curves such as Justes et al. (1994), but the coefficient, exponent,
crop scope and total-biomass basis must be confirmed before calling it an exact
implementation. Treat `Ncrit` as an internal indicator until units and use are
validated.

Open validation point: zero biomass produces infinite values.

## Data Preparation Formalisms

Implemented in: `sarra_py/data_preparation.py`.

- TAMSAT helpers load daily rainfall into `rain`, expected in mm day-1.
- AgERA5 helpers map local files to `tpMoy`, `ET0` and `rg`.
- The active AgERA5 loaders divide `rg` by 1000, documenting a local conversion
  to MJ m-2 day-1.
- Soil helpers reproject local rasters and project CSV tables to the rainfall
  grid. The local CSV mapping defines several soil parameters used by the model.
- Day length helpers compute daylight from date and latitude, with longitude
  fixed to 0.0, then broadcast to the grid.

Status: **Code-observed** for file handling and conversions. Dataset provenance,
local preprocessing and soil table units remain open validation points.

## References And Source Status

References below are grouped by use. Bibliographic details marked TODO should
be verified before adding exact titles, DOIs, URLs or page numbers.

### Direct SARRA Or SARRA-H Sources

- SARRA-H and SARRA-O repositories/documentation: source family for legacy model
  structure and Pascal procedure names. TODO: verify exact formalism page and
  citation details to use in published documentation.
- Dingkuhn et al. 2003; Baron et al. 2005; Kouressy et al. 2008; Lalou et al.
  2019. TODO: verify bibliographic details and which equations correspond to
  active SARRA-Py functions before citing as exact sources.

### FAO And Water Stress

- Allen, Pereira, Raes and Smith (1998), FAO Irrigation and Drainage Paper 56.
  Used as **Source-related** for p-factor, `Ks`-like stress, dual crop
  coefficient and soil-evaporation reduction families, not as an exact
  implementation claim.

### Land Surface Soil Evaporation

- Noah LSM soil evaporation formalism. TODO: verify exact bibliographic details
  and equation form before adding a precise citation. Used here only as
  **Source-related** context for power-law direct soil evaporation reductions
  based on normalized top-layer soil water, not as an implementation claim.

### Photoperiodism

- Dingkuhn et al. (2008). Used as **Source-related** for the sorghum
  "Impatience" model family.
- Folliard et al. 2004. TODO: verify details before citing beyond family-level
  context.

### Mulch

- Scopel, E., Da Silva, F. A. M., Corbeels, M., Affholder, F. and Maraux, F.
  (2004). Modelling crop residue mulching effects on water use and production
  of maize under semi-arid and humid tropical conditions. Agronomie, 24,
  383-395. Used as **Source-related** for crop-residue interception, mulch
  evaporation, radiation interception and runoff-reduction concepts; not as an
  exact SARRA-Py equation match.
- Ranaivoson et al. 2017. TODO: verify details before using beyond broad mulch
  context.

### Radiation And Biomass

- Monteith (1977); Sinclair and Muchow (1999). Used as broad
  **Source-related** references for radiation-use-efficiency and big-leaf
  modelling concepts, not for SARRA-Py conversion factors.

### Nitrogen

- Justes et al. (1994). Used as **Source-related** for critical nitrogen
  dilution curves. The active SARRA-Py `Ncrit` equation is not documented here
  as an exact implementation.
