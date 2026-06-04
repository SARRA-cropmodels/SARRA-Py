# Plan d'amelioration des docstrings SARRA-Py

Date d'audit: 2026-06-04

## Objectif

Homogeneiser les docstrings sans modifier les formalismes scientifiques ni le
comportement du modele. Ce document propose un standard et des exemples, mais
aucune docstring scientifique n'a ete appliquee au code pendant cet audit.

## Probleme actuel

Sur 150 fonctions auditees:

- 21 fonctions n'ont pas de docstring.
- 96 docstrings contiennent encore des placeholders (`_type_`,
  `_description_`, `_summary_`).
- Les unites, dimensions, variables `xarray` lues/ecrites et effets de bord sont
  rarement systematiques.
- Les references SARRA-H/Pascal/FAO/Alhassane/Dingkuhn/Justes sont presentes
  dans certaines fonctions mais pas dans un format stable.

Le plus important: les fonctions mutent presque toutes `data` en place. Cet
effet de bord doit etre indique explicitement.

## Standard propose

Style recommande: NumPy docstring style, avec sections scientifiques ajoutees
quand pertinent.

Template minimal:

```python
def function_name(...):
    """One-line summary.

    Longer explanation of the role in the SARRA-Py workflow.

    Parameters
    ----------
    j : int
        Daily time index. The first dataset dimension is expected to be time.
    data : xarray.Dataset or dict[str, numpy.ndarray]
        Simulation state. Expected dimensions are ``("time", "y", "x")`` for
        dynamic variables and ``("y", "x")`` for static variables.
    paramVariete : dict
        Variety parameters. Required keys: ...

    Reads
    -----
    data variables:
        ``rain`` [mm day-1], ``numPhase`` [-], ...

    Writes
    ------
    data variables:
        ``target_variable`` [unit]. Values are written in place on ``j`` or
        broadcast from ``j`` to the end of the simulation with ``j:``.

    Returns
    -------
    xarray.Dataset or dict[str, numpy.ndarray]
        The same object as ``data``, mutated in place.

    Scientific background
    ---------------------
    Describe the process and relation to SARRA-H/SARRA-Py.

    Equation
    --------
    Use plain text equations or short LaTeX-style notation.

    Assumptions
    -----------
    - Daily time step.
    - Spatially aligned arrays.
    - Units and parameter validity assumptions.

    Notes
    -----
    Mention edge cases, NaN handling, clipping, warnings and legacy behavior.

    References
    ----------
    Bibliographic references or source code provenance.
    """
```

Pour les fonctions purement logicielles:

- garder `Parameters`, `Returns`, `Raises`, `Notes`;
- ne pas ajouter `Scientific background`.

Pour les fonctions wrappers:

- lister l'ordre des fonctions appelees;
- expliquer pourquoi l'ordre est important;
- indiquer si le wrapper est appele par `run_model` ou par les notebooks.

## Conventions a documenter partout

- `data` est mute en place et retourne pour chainage.
- Les variables dynamiques sont attendues avec la dimension temporelle en
  premiere position.
- L'ecriture `data["var"][j:,:,:] = ...` propage l'etat courant sur les jours
  futurs.
- `engine="xarray"` est le defaut public; `engine="numpy"` est optionnel.
- Les sorties notebook doivent conserver variables, dimensions, coordonnees et
  metadonnees.
- Les valeurs NaN ne sont pas toutes traitees explicitement; beaucoup de
  `np.where` evaluent les deux branches.

## Priorite de documentation

### P0: API notebook et moteur

| Fonction | Pourquoi |
|---|---|
| `run_model` | entree principale; doit documenter `engine`, `progress`, effets de bord |
| `run_waterbalance_model` | entree publique alternative |
| `initialize_simulation` | cree la plupart des variables et metadonnees |
| `load_YAML_parameters` | chemins, effet `NI`, mutation parametres |
| `initialize_default_irrigation` | public, sans docstring |
| `calc_day_length_raster_fast` | public, sans docstring, cache interne |
| `calculate_once_daily_thermal_time` | public notebook; formule critique |

### P1: formalismes hydriques critiques

| Fonction | Pourquoi |
|---|---|
| `EvolRurCstr2` | croissance racinaire et stress hydrique |
| `update_root_tank_stock` | commentaire interne signale un doute majeur |
| `fill_tanks` | coeur des reservoirs |
| `compute_soil_evaporation` | wrapper sans docstring |
| `compute_transpiration` | wrapper sans docstring |
| `estimate_pFact` | lien FAO-56 |
| `estimate_cstr` | coefficient de stress hydrique |
| `ConsoResSep` | separation evaporation/transpiration |
| `update_plant_transpiration` | borne suspecte de transpiration |

### P1: formalismes carbone/rendement

| Fonction | Pourquoi |
|---|---|
| `update_assimPot` | conversion rayonnement -> biomasse; effet `NI` |
| `update_assim` | stress hydrique sur assimilation |
| `calculate_maintainance_respiration` | formalisme Q10 |
| `update_total_biomass` | cumul biomasse central |
| `update_potential_yield` | potentiel rendement |
| `update_potential_yield_delta` | demande journaliere rendement |
| `EvalFeuilleTigeSarrahV4` | partition feuilles/tiges |
| `calculate_canopy_specific_leaf_area` | SLA, divisions fragiles |
| `estimate_critical_nitrogen_concentration` | appelee par la boucle, sans docstring |

### P2: legacy, I/O et utilitaires

| Fonction | Pourquoi |
|---|---|
| `load_TAMSAT_data*`, `load_AgERA5_data*` | chemins, formats, cout I/O |
| `load_iSDA_soil_data*` | sources et conversion unites |
| `BiomDensOptSarraV4`, `BiomDensiteSarraV42`, `BiomMcUBTSV3`, `MAJBiomMcSV3` | legacy public non observe |
| fonctions multi-cycle hydriques non appelees | statut a clarifier |
| fonctions internes `models.py` | comprehension moteur NumPy |

## Exemples de docstrings proposes

Ces exemples sont des propositions. Ils ne doivent pas etre appliques sans
validation du vocabulaire scientifique.

### `run_model`

```python
def run_model(paramVariete, paramITK, paramTypeSol, data, duration,
              engine="xarray", progress=True):
    """Run the complete daily SARRA-Py crop simulation.

    The public notebook API accepts an initialized ``xarray.Dataset`` and returns
    the same dataset structure after applying phenology, water balance, carbon
    balance and yield calculations for ``duration`` daily time steps.

    Parameters
    ----------
    paramVariete : dict
        Variety parameters used by phenology, carbon balance and transpiration.
    paramITK : dict
        Crop management parameters, including sowing date, density and optional
        irrigation settings.
    paramTypeSol : dict
        Soil parameters. Kept for API compatibility; most spatial soil
        properties are expected in ``data``.
    data : xarray.Dataset
        Initialized simulation state. Dynamic variables are expected to have
        dimensions compatible with ``data["rain"].dims``.
    duration : int
        Number of daily time steps to simulate.
    engine : {"xarray", "numpy"}, default "xarray"
        Execution engine. ``"xarray"`` preserves the legacy behavior.
        ``"numpy"`` converts data variables to writable NumPy arrays internally
        and restores them into the dataset before returning.
    progress : bool, default True
        Display a progress bar over daily time steps.

    Returns
    -------
    xarray.Dataset
        The input dataset, mutated in place and returned for chaining.

    Notes
    -----
    This function does not prepare weather, soil, day length, irrigation or
    thermal time inputs. Existing notebooks usually call
    ``initialize_simulation``, ``calc_day_length_raster_fast``,
    ``initialize_default_irrigation`` and
    ``calculate_once_daily_thermal_time`` before ``run_model``.
    """
```

### `calc_day_length_raster_fast`

```python
def calc_day_length_raster_fast(data, date_start, duration):
    """Add gridded daily day length to the simulation dataset.

    Day length is computed for each simulation day and each latitude in
    ``data["y"]`` using ``calc_day_length``. The resulting ``(time, y)`` matrix
    is broadcast to the full shape and dimension order of ``data["rain"]`` and
    stored as ``data["dureeDuJour"]``.

    Parameters
    ----------
    data : xarray.Dataset
        Dataset containing ``rain`` and a latitude coordinate named ``y``.
    date_start : datetime.date or datetime.datetime
        First simulation date.
    duration : int
        Number of daily values to compute.

    Writes
    ------
    data["dureeDuJour"] : xarray.DataArray
        Day length in hours, with the same dimensions and shape as
        ``data["rain"]``.

    Returns
    -------
    xarray.Dataset
        The same dataset, mutated in place.

    Notes
    -----
    The internal day-by-latitude calculation is cached by date, duration and
    latitude tuple. This does not change values; it avoids recomputing static day
    length across climate scenarios using the same grid and dates.
    """
```

### `calculate_once_daily_thermal_time`

```python
def calculate_once_daily_thermal_time(data, paramVariete):
    """Compute daily thermal time for the whole simulation period.

    This vectorized helper fills ``data["ddj"]`` before the daily model loop.
    It is equivalent to applying ``calculate_daily_thermal_time`` at every time
    step when ``tpMoy`` is already available for the full period.

    Equation
    --------
    For mean daily temperature ``T = tpMoy``:

    ``ddj = max(min(TOpt1, T), TBase) - TBase`` if ``T <= TOpt2``.

    Otherwise:

    ``ddj = (TOpt1 - TBase) * (1 - (min(TLim, T) - TOpt2) /
    (TLim - TOpt2))``.

    Parameters
    ----------
    data : xarray.Dataset or dict[str, numpy.ndarray]
        Must contain ``tpMoy`` and writable ``ddj`` arrays with matching
        dimensions.
    paramVariete : dict
        Must contain ``TBase``, ``TOpt1``, ``TOpt2`` and ``TLim`` in degrees C.

    Writes
    ------
    data["ddj"] : same type as input storage
        Daily thermal time in degree-days.

    Notes
    -----
    The active implementation uses mean temperature only. Historical comments in
    the code mention a more detailed Tmin/Tmax formulation; switching formulas
    would be a scientific change requiring validation.
    """
```

### `estimate_pFact`

```python
def estimate_pFact(j, data, paramVariete):
    """Estimate the FAO-like depletion fraction threshold for water stress.

    ``pFact`` represents the fraction of total available water that can be
    depleted before transpiration stress starts. It is adjusted by evaporative
    demand and bounded to ``[0.1, 0.8]``.

    Equation
    --------
    ``pFact = PFactor + 0.04 * (5 - kcp * ET0)``

    ``pFact = min(max(pFact, 0.1), 0.8)``

    Parameters
    ----------
    j : int
        Daily time index.
    data : xarray.Dataset or dict[str, numpy.ndarray]
        Reads ``kcp`` [-] and ``ET0`` [mm day-1]. Writes ``pFact`` [-].
    paramVariete : dict
        Must contain ``PFactor`` [-].

    Scientific background
    ---------------------
    This follows the FAO-56 idea of adjusting the readily available water
    fraction ``p`` according to crop evapotranspiration demand. SARRA-Py applies
    the adjustment to ``kcp * ET0``.

    References
    ----------
    Allen et al. (1998), FAO Irrigation and Drainage Paper 56, Chapter 8.
    """
```

### `update_plant_transpiration`

```python
def update_plant_transpiration(j, data):
    """Adjust plant transpiration according to available root-zone water.

    Parameters
    ----------
    j : int
        Daily time index.
    data : xarray.Dataset or dict[str, numpy.ndarray]
        Reads ``tr`` [mm day-1] and ``root_tank_stock`` [mm]. Writes ``tr``.

    Notes
    -----
    The current implementation sets ``tr`` to
    ``max(root_tank_stock - tr, 0)`` when transpiration demand exceeds available
    root-tank stock. Existing comments in the source question this rule and
    suggest that ``min(tr, root_tank_stock)`` may be more intuitive. This
    docstring should not be applied until the intended scientific behavior is
    validated.
    """
```

### `estimate_critical_nitrogen_concentration`

```python
def estimate_critical_nitrogen_concentration(j, data):
    """Estimate critical nitrogen concentration from plant biomass.

    Equation
    --------
    ``Ncrit = 5.35 * (biomasseTotale / 1000) ** (-0.44)``

    Parameters
    ----------
    j : int
        Daily time index.
    data : xarray.Dataset or dict[str, numpy.ndarray]
        Reads ``biomasseTotale`` [kg ha-1]. Writes ``Ncrit`` [% dry matter].

    Scientific background
    ---------------------
    The coefficients match the critical nitrogen dilution curve reported by
    Justes et al. (1994) for winter wheat, where dry matter is expressed in
    t ha-1.

    Notes
    -----
    The original Justes curve was derived for shoot biomass and a limited biomass
    range. SARRA-Py currently applies it to ``biomasseTotale`` and does not guard
    biomass equal to zero; this can produce infinite values.

    References
    ----------
    Justes et al. (1994), Annals of Botany, DOI 10.1006/anbo.1994.1133.
    """
```

## Sources bibliographiques a relier aux docstrings

- FAO-56 chapitre 8 pour `estimate_pFact`, `estimate_cstr`,
  `estimate_plant_transpiration`, et les notes sur `Ks`, `TAW`, `RAW`.
- Dingkuhn et al. (2008) pour `update_photoperiodism`, mais uniquement apres
  validation que la formule SARRA-Py correspond bien a la variante souhaitee.
- Justes et al. (1994) pour `estimate_critical_nitrogen_concentration`, avec
  avertissement sur culture et biomasse.
- Leenaars et al. (2018) et iSDAsoil pour `load_iSDA_soil_data*`.
- Documentation SARRA-H/Pascal historique, a identifier dans le depot ou les
  archives projet, pour les coefficients rendement, SLA, densite et mulch.

## Questions avant modification des docstrings scientifiques

1. Souhaite-t-on documenter les fonctions elementaires comme API publique, ou les
   marquer comme internes/legacy tout en gardant les imports?
2. Faut-il conserver les mentions explicites de doutes scientifiques dans les
   docstrings, ou les deplacer dans une section `Notes`/`Known limitations`?
3. Quelle nomenclature adopter pour les variables francaises historiques
   (`rdt`, `cstr`, `sdj`) et leurs noms longs anglais?
4. Les references au code Pascal original doivent-elles pointer vers des fichiers
   disponibles publiquement ou rester sous forme de provenance interne?
5. Peut-on ajouter une section "Mutates" ou prefere-t-on "Writes" pour les
   variables `xarray` modifiees?
