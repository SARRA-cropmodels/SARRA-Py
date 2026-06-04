# SARRA-Py Model Formalisms

This document is the maintained scientific overview for SARRA-Py. It describes
the active equations observed in the code without changing them. Raw audit notes
are archived under `docs/dev/audits/`.

SARRA-Py is a daily, spatial crop model run from notebook workflows on xarray
inputs. The public API returns xarray outputs; `engine="xarray"` remains the
default, while `engine="numpy"` is an internal acceleration option.

## State And Time Step

Dynamic variables are simulated on a daily time axis and a spatial grid. Most
scientific functions mutate the model state in place and often propagate the
current value from day `j` to the end of the simulation with `j:`.

Main process order in `run_model`:

1. Phenology and thermal-time accumulation.
2. Irrigation, rainfall input, mulch interception, runoff and reservoir filling.
3. Soil evaporation, transpiration and water consumption.
4. Carbon assimilation, biomass partitioning, LAI and yield.
5. Photoperiodism, mortality and nitrogen indicator.

## Phenology

The crop cycle is represented by phases `0` to `7`: no crop, initialization /
germination, vegetative development, photoperiod-sensitive phase, reproductive
phase, filling/maturation steps and harvest.

Transitions mainly compare accumulated thermal time `sdj` with variety
thresholds such as `SDJLevee`, `SDJBVP`, `SDJRPR`, `SDJMatu1` and `SDJMatu2`.
The code writes phase changes from the current day onward, so the daily order is
part of the numerical behaviour.

Daily thermal time currently uses mean temperature `tpMoy`:

```text
if tpMoy <= TOpt2:
    ddj = max(min(TOpt1, tpMoy), TBase) - TBase
else:
    ddj = (TOpt1 - TBase)
          * (1 - ((min(TLim, tpMoy) - TOpt2) / (TLim - TOpt2)))
```

Temperatures are in degrees Celsius and `ddj` is in degree-days per day. Older
comments mention a Tmin/Tmax formulation; this remains an open validation point.

Day length is computed with Astral sunrise/sunset daylight duration from date
and latitude, then broadcast to the rainfall grid. Photoperiodism is related to
the sorghum "Impatience" family of models, but the exact SARRA-Py equation and
thresholds should be validated before being cited as an implementation of a
specific publication.

## Water Balance

The hydrological state is represented by surface, total/deep and root-accessible
reservoirs. Water inputs are daily rainfall plus irrigation:

```text
available_water = rain + irrigTotDay
```

The conceptual daily balance is:

```text
stock(d+1) = stock(d) + inputs - runoff - drainage - evaporation - transpiration
```

Actual code uses several overlapping reservoirs, so this equation is a guide,
not a one-to-one variable identity.

### Soil Evaporation

Surface evaporable water:

```text
fesw = surface_tank_stock / surface_tank_capacity
```

Soil evaporation coefficient:

```text
kce = ltr * mulch * exp(-coefMc * surfMc * biomMc / 1000)
```

Potential and actual soil evaporation:

```text
evapPot = ET0 * kce
evap = min(evapPot * fesw**2, surface_tank_stock)
```

These equations are related to FAO-56 soil evaporation concepts, but the squared
`fesw` response and mulch term are SARRA-Py current implementation details.

### Transpiration And Water Stress

Root reservoir filling:

```text
ftsw = root_tank_stock / root_tank_capacity
```

The p-factor follows the FAO-56 adjustment form, expressed with SARRA-Py demand:

```text
pFact = PFactor + 0.04 * (5 - kcp * ET0)
pFact = clip(pFact, 0.1, 0.8)
```

Water stress and transpiration:

```text
cstr = clip(ftsw / (1 - pFact), 0, 1)
trPot = kcp * ET0
tr = trPot * cstr
```

This is close to the FAO-56 `p`/`Ks` family, but SARRA-Py uses reservoir filling
rather than root-zone depletion variables.

### Root Reservoir And Humectation Front

Root reservoir capacity grows from phase-dependent root growth speed `vRac`,
soil available-water capacity `ru`, water stress and the humectation front:

```text
delta_root_tank_capacity = vRac / 1000 * ru
if root_tank_capacity > surface_tank_capacity:
    delta_root_tank_capacity *= min(cstr + 0.3, 1.0)
delta_root_tank_capacity =
    min(delta_root_tank_capacity, humectation_front - root_tank_capacity)
```

The subsequent update of `root_tank_stock` mixes capacity and stock terms and is
listed in `docs/scientific_validation_questions.md`.

### Runoff, Drainage And Mulch

Runoff is threshold based:

```text
if rain > runoff_threshold:
    runoff = (available_water - runoff_threshold) * runoff_rate
else:
    runoff = 0
```

The trigger uses rainfall while the amount uses `available_water`; this is an
open validation point for irrigated or mulched scenarios.

Mulch interception uses an exponential cover term and local unit conversions:

```text
water_captured_by_mulch =
    min(
        available_water * (1 - exp(-surfMc / 1000 * biomMc)),
        humSatMc * biomMc / 10000 - mulch_water_stock
    )
```

The mulch formalism remains less well sourced than the FAO-like stress terms.

## Carbon Balance

Carbon assimilation uses a big-leaf representation. The non-intercepted light
fraction is:

```text
ltr = exp(-kdf * lai)
```

Potential assimilation:

```text
PAR = 0.5 * rg
assimPot = PAR * (1 - exp(-kdf * lai)) * conv * 10
```

`rg` is expected in MJ m-2 day-1. The `0.5` PAR fraction and `10` conversion
factor are common modelling choices but should remain tied to SARRA-Py
calibration.

Water stress scales assimilation:

```text
assim = assimPot * tr / trPot
```

when `trPot > 0`; otherwise assimilation is set to zero by the active code.

Maintenance respiration uses a Q10-like temperature response:

```text
respMaint = kRespMaint * biomasseTotale * 2**((tpMoy - tempMaint) / 10)
```

Daily total biomass then follows:

```text
biomasseTotale(d+1) = biomasseTotale(d) + assim - respMaint
```

with additional bounds and phase conditions in the code.

## Biomass Partition, LAI And Yield

Aboveground, root, leaf and stem biomasses are updated through phase-dependent
empirical rules. Around and after flowering, reallocation and grain filling
rules move biomass toward yield variables.

Specific leaf area (SLA) is interpolated from variety parameters and current
vegetative state. LAI is derived from leaf biomass and SLA:

```text
lai = surfaceFeuille / 10000
```

where `surfaceFeuille` is produced from leaf biomass and SLA. Zero-biomass cases
can trigger numerical warnings and are listed in the validation questions.

Potential yield and daily filling demand are central agronomic outputs but were
not matched to a public exact equation during the audit. Treat their current
docstrings as descriptions of active code, not independent scientific
validation.

## Nitrogen Indicator

The current critical nitrogen concentration implementation uses:

```text
Ncrit = 5.35 * (biomasseTotale / 1000)**(-0.44)
```

Earlier audit notes compare this to critical nitrogen dilution curves such as
Justes et al. (1994), but the active equation and biomass basis are not an exact
match and need validation before stronger claims are made.

## Data Preparation Formalisms

TAMSAT helpers load daily rainfall rasters into `data["rain"]`, expected in mm.

AgERA5 helpers map local forcing folders to:

- `tpMoy`: mean daily temperature.
- `ET0`: reference evapotranspiration.
- `rg`: solar radiation, divided by 1000 in the current loaders to convert the
  local files to MJ m-2 day-1.

iSDA and Africa soil-grid helpers reproject local soil rasters and project CSV
tables to the rainfall grid. Dataset provenance and local table units should be
confirmed before adding stronger scientific claims.

## References

- Allen, R. G., Pereira, L. S., Raes, D. & Smith, M. (1998). FAO Irrigation and
  Drainage Paper 56, *Crop evapotranspiration*.
- Dingkuhn, M. et al. (2008). Sorghum photoperiodism and the "Impatience" model
  family; used here only as a related-family reference.
- Justes, E. et al. (1994). Critical nitrogen dilution curve; related to the
  current N indicator but not an exact match.
- Maidment, R. I. et al. (2017). TAMSAT rainfall estimates.
- Astral documentation for daylight duration calculations.
