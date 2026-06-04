# Opportunites de refactoring SARRA-Py

Date d'audit: 2026-06-04

## Contraintes retenues

- Ne pas changer les resultats scientifiques sans validation.
- Ne pas changer le defaut public `engine="xarray"`.
- Ne pas casser `from sarra_py import *` ni les notebooks existants.
- Ne pas faire de refactor global.
- Prioriser les refactors lisibles, testables, et compatibles avec le moteur
  `engine="numpy"`.

Statuts:

- `propose_only`: proposition documentaire, non implementee.
- `needs_validation`: demande validation scientifique/API avant code.
- `implement_now`: suffisamment faible risque pour une petite PR dediee.

## P0: corrections structurelles a planifier

| Proposition | Effort | Risque | Impact attendu | Tests necessaires | Benchmark | Statut |
|---|---:|---:|---|---|---|---|
| Definir une surface API explicite avec `__all__` tout en conservant les noms notebook | moyen | moyen API | reduit l'exposition accidentelle de fonctions legacy | test import notebook, `from sarra_py import *`, inventaire API | non | needs_validation |
| Documenter et tester les invariants de dimensions `("time", "y", "x")` | petit | faible | evite erreurs silencieuses de grille | tests dimensions/coords sur `initialize_simulation`, run engines | non | implement_now |
| Ajouter une table centrale des variables creees par `initialize_simulation` | moyen | faible | clarifie unites, attrs, sorties | tests attrs/vars existantes | non | propose_only |
| Ecrire des tests de bilan hydrique simple sur une cellule sans pluie/avec pluie | moyen | moyen scientifique | detecte creation/perte d'eau grossiere | tests unitaires hydriques par fonctions wrappers | non | needs_validation |
| Isoler la politique `engine` dans docstrings et tests API | petit | faible | evite regression du defaut `xarray` | tests `run_model.__defaults__`, smoke imports | non | implement_now |

## P0 scientifique: ne pas modifier sans validation

| Fonction/zone | Probleme observe | Risque si modifiee | Action proposee | Statut |
|---|---|---:|---|---|
| `update_root_tank_stock` | commentaire interne signale un melange stock/capacite et possible creation d'eau | fort | creer cas pedagogique 1 pixel et comparer avec reference SARRA-H | needs_validation |
| `update_plant_transpiration` | si `tr > root_tank_stock`, code met `tr=max(root_tank_stock-tr,0)` | fort | demander validation: comportement actuel vs `min(tr, root_tank_stock)` | needs_validation |
| `calculate_once_daily_thermal_time` | docstring mentionne une formule Tmin/Tmax differente du code actif `tpMoy` | fort | figer la formule active par tests et demander choix scientifique | needs_validation |
| `estimate_fesw` / `update_surface_tank_stock` | docstrings 110%, code 100% | moyen | clarifier si le code ou la doc est la reference | needs_validation |
| `estimate_critical_nitrogen_concentration` | Justes ble hiver, code sur `biomasseTotale`, biomasse nulle non protegee | moyen/fort | demander si l'indicateur azote doit rester diagnostic ou devenir sortie officielle | needs_validation |

## P1: refactors logiciels a faible risque relatif

| Proposition | Effort | Risque | Impact attendu | Tests necessaires | Benchmark | Statut |
|---|---:|---:|---|---|---|---|
| Extraire un helper interne `allocate_like_rain(data, fill, dtype)` pour `initialize_simulation` | moyen | faible/moyen | reduit duplication `np.full`, centralise dims | tests vars/dims/attrs/allclose | oui, helper prep | propose_only |
| Remplacer les chemins relatifs YAML par resolution configurable depuis racine projet, avec compatibilite | moyen | moyen API | rend package moins dependant du cwd notebook | tests chargement anciens chemins + chemins absolus | non | needs_validation |
| Ajouter wrappers internes pour `data["var"][j,:,:]` / ecriture `j:` | grand | moyen | clarifie semantics xarray/NumPy | regression engines xarray/numpy | oui | propose_only |
| Deplacer la creation de `total_tank_capacity` hors de `fill_tanks` vers initialisation | petit/moyen | scientifique moyen | retire recalcul conditionnel j==0 | tests stricts hydriques | non | needs_validation |
| Factoriser `compute_soil_evaporation` et `compute_transpiration` avec docstrings wrappers | petit | faible | lisibilite forte | tests imports + smoke model | non | implement_now |

## P1: performance sans changement scientifique

| Proposition | Effort | Risque | Impact attendu | Tests necessaires | Benchmark | Statut |
|---|---:|---:|---|---|---|---|
| Benchmark dedie `initialize_simulation` par taille de grille | petit | faible | quantifie allocations | smoke benchmark | oui | propose_only |
| Vectoriser ou cacher mapping `soil_type -> soil variables` dans `load_iSDA_soil_data*` | moyen | moyen I/O | acceleration prep sol | allclose cartes sol, coords, attrs | oui, realistic prep | propose_only |
| Eviter `xr.concat` en boucle dans `load_TAMSAT_data` et `load_AgERA5_data` | moyen | moyen I/O | acceleration donnees historiques | tests avec mini rasters temporaires | oui I/O | propose_only |
| Cache copy-safe pour YAML | petit | faible/moyen | evite I/O repetee notebooks multi-scenarios | tests mutation param dicts | micro-benchmark | propose_only |
| Profil ligne par ligne des wrappers `EvolRurCstr2`, `fill_tanks`, `ConsoResSep` sous engine NumPy | petit | faible | cible les prochaines optimisations | aucun changement code | oui | propose_only |

## P2: nettoyage legacy

| Fonction/zone | Probleme | Proposition | Risque | Statut |
|---|---|---|---:|---|
| `BiomDensOptSarraV4` | retourne `data`, corps utile commente | documenter legacy ou deprecier | moyen API | needs_validation |
| `EvalAssimSarrahV4` | corps utile dans docstring, retourne `data` | documenter legacy ou supprimer de `__all__` futur | moyen API | needs_validation |
| `BiomDensiteSarraV42` | non appelee, sans docstring, duplication `adjust_for_sowing_density` | marquer legacy | moyen API | needs_validation |
| `BiomMcUBTSV3`, `MAJBiomMcSV3` | legacy mulch/UBT non appele | garder en module experimental/documenter | moyen scientifique | needs_validation |
| fonctions multi-cycle hydriques | non appelees car code simplifie | deplacer vers section legacy documentee | moyen scientifique | needs_validation |
| `reset` | non appelee, fait `copy(deep=True)` | verifier historique; documenter ou deprecier | faible/moyen | propose_only |

## P2: qualite numerique

| Zone | Symptome | Proposition | Risque | Tests |
|---|---|---|---:|---|
| `np.where` avec divisions | warnings car deux branches evaluees | utiliser masques ou `np.divide(..., where=...)` apres validation | moyen | allclose strict + warning tests |
| `~np.isnan(...)` | peu lisible, fragile pour non-float | remplacer par helper `is_defined_number` | faible/moyen | tests parametres NaN/non-NaN |
| biomasse nulle dans `Ncrit` | inf attendu | definir politique: NaN, inf, zero, ou masque phase | fort scientifique | validation scientifique |
| divisions `SeuilPP - PPCrit`, `TLim - TOpt2` | pas de garde | validation parametres en entree | moyen API | tests erreurs explicites |
| mutation de `paramVariete["txConversion"]` | effet de bord cache | calculer localement ou documenter mutation | moyen scientifique | tests equivalence + mutation |

## P2: documentation technique

| Proposition | Effort | Risque | Impact | Statut |
|---|---:|---:|---|---|
| Ajouter `docs/variables_reference.md` genere depuis `variable_dict` et variables sol/meteo | moyen | faible | documentation sorties | propose_only |
| Ajouter diagramme de daily loop dans docs | petit | faible | comprehension modeles | propose_only |
| Ajouter page "Notebook API compatibility" | petit | faible | clarifie workflows | propose_only |
| Ajouter page "Scientific validation questions" maintenue | petit | faible | traque decisions | propose_only |

## Tests recommandes par niveau

### Tests unitaires invariants

- Toutes les fonctions helpers publiques conservent type, dims, coords, attrs
  attendus.
- `initialize_simulation` cree les memes variables avec les memes dims et attrs.
- `run_model(engine="xarray")` et `run_model(engine="numpy")` restent
  numeriquement equivalents sur cas tiny/small.

### Tests scientifiques reduits

- Cas 1 pixel sans pluie: pas de stock negatif, pas de rendement non explicable.
- Cas 1 pixel pluie unique: conservation approximative du bilan eau
  `rain + irrigation = runoff + drainage + evap + tr + delta_stock`.
- Cas phenologie: transitions de phases sur seuils thermiques controles.
- Cas photoperiodisme: `sumPP` et `phasePhotoper` sur latitudes et dates
  controlees.

### Benchmarks

- `benchmarks/benchmark_run_model.py`: garder pour engines.
- `benchmarks/benchmark_helpers.py`: etendre pour `initialize_simulation`,
  YAML, sol et meteo si des refactors sont faits.
- `benchmarks/benchmark_exemple_12.py`: garder realistic manuel.

## Recommandation d'ordre de travail

1. Stabiliser la documentation API et les docstrings P0 sans changer la logique.
2. Ajouter tests invariants sur `initialize_simulation` et wrappers hydriques.
3. Demander validation scientifique sur `update_root_tank_stock`,
   `update_plant_transpiration`, temps thermique, FESW 100/110% et Ncrit.
4. Factoriser seulement les allocations et helpers qui sont couverts par tests
   de non-regression.
5. Definir `__all__` seulement apres inventaire externe ou periode de
   compatibilite.

## Changements non recommandes maintenant

- Passer `engine="numpy"` par defaut sans nouvelle validation realistic.
- Introduire Numba avant stabilisation des docstrings, tests et invariants.
- Recrire le bilan hydrique en une seule passe.
- Supprimer les fonctions legacy sans deprecation.
- Corriger les formalismes suspects directement, meme s'ils semblent
  intuitivement faux, sans comparaison SARRA-H et validation metier.
