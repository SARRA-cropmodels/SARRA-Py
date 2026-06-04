# Audit des fonctions du package SARRA-Py

Date d'audit: 2026-06-04

## Portee et methode

Cet audit couvre tous les fichiers Python de `src/sarra_py`: `models.py`,
`data_preparation.py`, `bilan_pheno.py`, `bilan_hydro.py` et
`bilan_carbo.py`. Les notebooks ont ete inspectes uniquement pour identifier les
usages reels de l'API publique.

Extraction automatique utilisee:

- analyse AST des fonctions top-level, signatures, docstrings et appels;
- recherche statique des appels directs dans `notebooks/*.ipynb`;
- recherche de patterns de risque: `xr.where`, `np.where`, ecritures
  `data["var"][j:,:,:]`, `copy(deep=True)`, `xr.concat`,
  `open_mfdataset`, `reproject_match`, chemins relatifs;
- lecture manuelle des fonctions scientifiques critiques.

Limites: le graphe d'appels est statique et approximatif. Les appels indirects
par `from sarra_py import *`, les fonctions passees comme objets et les usages
externes hors depot ne sont pas tous observables.

## Resume quantitatif

| Module | Fonctions |
|---|---:|
| `sarra_py.bilan_hydro` | 62 |
| `sarra_py.bilan_carbo` | 40 |
| `sarra_py.bilan_pheno` | 20 |
| `sarra_py.data_preparation` | 18 |
| `sarra_py.models` | 10 |
| **Total** | **150** |

Visibilite effective:

- 138 fonctions ont un nom public, car elles ne commencent pas par `_`.
- 12 fonctions sont privees par convention.
- `src/sarra_py/__init__.py` importe les modules avec `*`; en l'absence de
  `__all__`, presque toutes les fonctions non privees deviennent importables
  depuis `sarra_py`, y compris des fonctions scientifiques de bas niveau et des
  fonctions legacy non appelees.

Qualite des docstrings detectee automatiquement:

| Etat docstring | Nombre |
|---|---:|
| Docstring avec placeholders (`_type_`, `_description_`, `_summary_`) | 96 |
| Docstring partielle | 21 |
| Absente | 21 |
| Bonne base | 7 |
| Vague | 5 |

Cette classification est volontairement stricte: une docstring peut contenir une
description scientifique utile tout en etant classee "partielle/placeholders" si
ses sections `Args` ou `Returns` restent non renseignees.

## Fonctions publiques utilisees dans les notebooks

Les notebooks appellent surtout une API notebook stable:

| Fonction | Appels directs notebooks | Role |
|---|---:|---|
| `initialize_simulation` | 21 | initialisation de l'etat de simulation |
| `calc_day_length_raster_fast` | 21 | longueur du jour grillee |
| `initialize_default_irrigation` | 21 | irrigation par defaut |
| `calculate_once_daily_thermal_time` | 21 | temps thermique journalier pre-calcule |
| `load_YAML_parameters` | 21 | chargement parametres |
| `run_model` | 19 | modele complet |
| `get_grid_size` | 11 | taille grille raster historique |
| `load_TAMSAT_data` | 11 | pluie raster historique |
| `load_AgERA5_data` | 11 | meteo raster historique |
| `load_iSDA_soil_data_alternate` | 11 | sols iSDA/RZPAWC |
| `load_iSDA_soil_data` | 7 | sols iSDA historique |
| `run_waterbalance_model` | 2 | modele bilan hydrique |

Conclusion API: ces noms doivent rester importables depuis `sarra_py`. Les
fonctions internes appelees uniquement par la boucle peuvent etre documentees ou
eventuellement privatisees plus tard, mais pas sans politique de compatibilite.

## Inventaire par module

Legende:

- Visibilite: `public` signifie importable par nom depuis le module et
  probablement depuis `sarra_py`.
- Doc: `absente`, `vague`, `partielle`, `partielle/placeholders`, `bonne base`.
- Risque: `API`, `scientifique`, `moyen`, `faible`, `interne`.
- Appels: `loop` = appelee depuis la boucle modele; `wrapper` = appelee depuis
  une fonction wrapper du meme module; `notebook` = appelee directement dans les
  notebooks.

### `sarra_py.models`

| Fonction | Signature | Visibilite | Appels | Role | Doc | Risque |
|---|---|---|---|---|---|---|
| `_normalize_engine` | `(engine)` | interne | `_run_with_engine` | normalisation option moteur | absente | interne |
| `_dataset_to_numpy_state` | `(data)` | interne | `_run_with_engine` | conversion xarray vers dict NumPy | absente | interne/performance |
| `_restore_numpy_state` | `(data, state)` | interne | `_run_with_engine` | restauration xarray | absente | interne/API sortie |
| `_infer_dims_from_shape` | `(data, shape)` | interne | `_restore_numpy_state` | inference dimensions | absente | interne/API sortie |
| `_run_loop` | `(iterator, data, paramVariete, paramITK, paramTypeSol)` | interne | indirect | orchestration daily loop complete | absente | scientifique/API interne |
| `_run_waterbalance_loop` | `(iterator, data, paramVariete, paramITK, paramTypeSol)` | interne | indirect | orchestration daily loop hydrique | absente | scientifique/API interne |
| `_make_iterator` | `(duration, progress)` | interne | `_run_with_engine` | progression | absente | faible |
| `_run_with_engine` | `(loop, paramVariete, paramITK, paramTypeSol, data, duration, engine, progress)` | interne | `run_model`, `run_waterbalance_model` | dispatch xarray/numpy | absente | API/performance |
| `run_model` | `(paramVariete, paramITK, paramTypeSol, data, duration, engine="xarray", progress=True)` | public | notebook | entree modele complet | partielle/placeholders | API eleve |
| `run_waterbalance_model` | `(paramVariete, paramITK, paramTypeSol, data, duration, engine="xarray", progress=True)` | public | notebook | entree modele hydrique | partielle/placeholders | API eleve |

Observations:

- Le defaut public `engine="xarray"` est conserve.
- Les fonctions moteur privees n'ont pas de docstrings alors qu'elles portent la
  compatibilite xarray/NumPy.
- `_restore_numpy_state` infere les dimensions par forme; risque silencieux si
  deux variables de dimensions differentes partagent la meme forme.

### `sarra_py.data_preparation`

| Fonction | Signature | Visibilite | Appels | Role | Doc | Risque |
|---|---|---|---|---|---|---|
| `build_rainfall_files_df` | `(rainfall_path, date_start, duration)` | public | wrappers | listing fichiers pluie | partielle/placeholders | faible |
| `get_grid_size` | `(rainfall_path, date_start, duration)` | public | notebook | taille grille historique | partielle/placeholders | API faible |
| `load_TAMSAT_data` | `(data, TAMSAT_path, date_start, duration)` | public | notebook | chargement pluie GeoTIFF | partielle/placeholders | I/O moyen |
| `load_TAMSAT_data_fast` | `(data, rainfall_data_path, date_start, duration)` | public | non observe | chargement pluie `open_mfdataset` | partielle/placeholders | I/O moyen |
| `load_AgERA5_data` | `(data, AgERA5_data_path, date_start, duration)` | public | notebook | chargement meteo GeoTIFF | partielle/placeholders | I/O moyen |
| `load_AgERA5_data_fast_dask` | `(data, AgERA5_data_path, date_start, duration)` | public | non observe | chargement meteo dask | partielle/placeholders | I/O/performance |
| `load_paramVariete` | `(file_paramVariete)` | public | `load_YAML_parameters` | YAML variete | partielle/placeholders | chemin/API |
| `load_paramITK` | `(file_paramITK)` | public | `load_YAML_parameters` | YAML ITK | partielle/placeholders | chemin/API |
| `load_paramTypeSol` | `(file_paramTypeSol)` | public | `load_YAML_parameters` | YAML sol | partielle/placeholders | chemin/API |
| `load_YAML_parameters` | `(file_paramVariete, file_paramITK, file_paramTypeSol)` | public | notebook | wrapper parametres | partielle/placeholders | API |
| `initialize_default_irrigation` | `(data)` | public | notebook | irrigation = 0 | absente | API faible |
| `load_iSDA_soil_data` | `(data, grid_width, grid_height)` | public | notebook | sols iSDA historique | partielle/placeholders | I/O/scientifique |
| `load_iSDA_soil_data_alternate` | `(data, grid_width, grid_height)` | public | notebook | sols iSDA + RZPAWC | partielle/placeholders | I/O/scientifique |
| `calc_day_length` | `(day, lat)` | public | helper | longueur jour ponctuelle | partielle/placeholders | faible scientifique |
| `_normalize_day_length_date` | `(date_start)` | interne | helper | cle cache | absente | faible |
| `_cached_day_length_matrix` | `(date_start_key, duration, latitudes)` | interne | helper | cache jour-latitude | absente | faible |
| `_broadcast_day_length_to_rain` | `(day_length_by_latitude, rain)` | interne | helper | broadcast vers dims pluie | absente | faible/API dimensions |
| `calc_day_length_raster_fast` | `(data, date_start, duration)` | public | notebook | longueur jour raster | absente | API/scientifique |

Observations:

- Chemins relatifs `../data/...` codes en dur dans les chargements YAML et sol.
- `load_paramVariete` leve une exception non documentee si
  `feuilAeroBase == 0.1`.
- `load_TAMSAT_data` et `load_AgERA5_data` concatennent dans une boucle.
- Les fonctions rapides avec dask existent mais ne sont pas observees dans les
  notebooks et leur statut public n'est pas clarifie.
- `calc_day_length_raster_fast` est critique pour les notebooks et n'a pas de
  docstring.

### `sarra_py.bilan_pheno`

| Fonction | Signature | Visibilite | Appels | Role | Doc | Risque |
|---|---|---|---|---|---|---|
| `_to_numpy` | `(values)` | interne | temps thermique | adaptation xarray/NumPy | absente | interne |
| `reset` | `(j, data)` | public | non observe | reset phenologie | absente | scientifique moyen |
| `testing_for_initialization` | `(j, data, paramITK, paramVariete)` | public | wrapper | passage phase 0 -> 1 | partielle/placeholders | scientifique |
| `flag_change_phase` | `(j, data, num_phase)` | public | wrapper | flag transition | partielle/placeholders | scientifique |
| `update_thermal_time_next_phase` | `(j, data, num_phase, thermal_time_threshold)` | public | wrapper | seuil prochaine phase | partielle/placeholders | scientifique |
| `increment_phase_number` | `(j, data)` | public | wrapper | increment `numPhase` | partielle/placeholders | scientifique |
| `update_thermal_time_previous_phase` | `(j, data, num_phase)` | public | wrapper | seuil phase precedente | partielle/placeholders | scientifique |
| `update_pheno_phase_1_to_2` | `(j, data, paramVariete)` | public | wrapper | levee | partielle/placeholders | scientifique |
| `update_pheno_phase_2_to_3` | `(j, data, paramVariete)` | public | wrapper | BVP -> PSP | partielle/placeholders | scientifique |
| `update_pheno_phase_3_to_4` | `(j, data)` | public | wrapper | fin PSP photoperiodique | partielle/placeholders | scientifique |
| `update_pheno_phase_4_to_5` | `(j, data, paramVariete)` | public | wrapper | RPR -> maturation | partielle/placeholders | scientifique |
| `update_pheno_phase_5_to_6` | `(j, data, paramVariete)` | public | wrapper | maturation 1 -> 2 | partielle/placeholders | scientifique |
| `update_pheno_phase_6_to_7` | `(j, data, paramVariete)` | public | wrapper | recolte | partielle/placeholders | scientifique |
| `EvalPhenoSarrahV3` | `(j, data, paramITK, paramVariete)` | public | loop | wrapper phenologie | bonne base | scientifique eleve |
| `calculate_daily_thermal_time` | `(j, data, paramVariete)` | public | waterbalance loop | degres-jour quotidien | partielle/placeholders | scientifique |
| `calculate_once_daily_thermal_time` | `(data, paramVariete)` | public | notebook | degres-jour pre-calcule | partielle/placeholders | API/scientifique |
| `calculate_sum_of_thermal_time` | `(j, data)` | public | loop | cumul degres-jour | partielle/placeholders | scientifique |
| `update_root_growth_speed` | `(j, data, paramVariete)` | public | loop | vitesse racinaire par phase | partielle/placeholders | scientifique |
| `update_photoperiodism` | `(j, data, paramVariete)` | public | loop | impatience photoperiodique | partielle/placeholders | scientifique eleve |
| `MortaliteSarraV3` | `(j, data, paramITK, paramVariete)` | public | loop | mortalite juvenile | partielle/placeholders | scientifique |

Observations:

- Les phases 0 a 7 sont bien decrites dans `EvalPhenoSarrahV3`, mais les
  fonctions elementaires restent publiques et peu documentees.
- Beaucoup d'ecritures propagent l'etat futur avec `data["var"][j:,:,:]`.
  C'est une convention centrale du modele et doit etre explicitee partout.
- `reset` fait un `copy(deep=True)` et semble non appelee.
- La formule de temps thermique signale encore `Pb de methode !?` dans la
  docstring; validation scientifique necessaire avant toute reformulation.

### `sarra_py.bilan_hydro`

| Fonction | Signature | Visibilite | Appels | Role | Doc | Risque |
|---|---|---|---|---|---|---|
| `InitPlotMc` | `(data, grid_width, grid_height, paramITK, paramTypeSol, duration)` | public | non observe | init reservoirs legacy | partielle | moyen |
| `update_irrigation_tank_stock` | `(j, data)` | public | wrapper | reservoir irrigation stock | partielle | scientifique |
| `update_irrigation_tank_capacity` | `(j, data)` | public | wrapper | reservoir irrigation capacite | partielle | scientifique |
| `compute_daily_irrigation` | `(j, data, paramITK)` | public | wrapper | dose irrigation auto | partielle | scientifique |
| `compute_irrigation_state` | `(j, data, paramITK)` | public | loop | wrapper irrigation | bonne base | scientifique |
| `compute_total_available_water` | `(j, data)` | public | loop | pluie + irrigation | bonne base | scientifique |
| `compute_water_captured_by_mulch` | `(j, data, paramITK)` | public | wrapper | interception mulch | partielle/placeholders | scientifique |
| `update_available_water_after_mulch_filling` | `(j, data)` | public | wrapper | eau apres mulch | partielle/placeholders | scientifique |
| `update_mulch_water_stock` | `(j, data)` | public | wrapper | stock eau mulch | partielle/placeholders | scientifique |
| `fill_mulch` | `(j, data, paramITK)` | public | loop | wrapper mulch | partielle | scientifique |
| `estimate_runoff` | `(j, data)` | public | wrapper | ruissellement seuil | partielle/placeholders | scientifique |
| `update_available_water_after_runoff` | `(j, data)` | public | wrapper | eau apres runoff | partielle/placeholders | scientifique |
| `compute_runoff` | `(j, data)` | public | loop | wrapper runoff | partielle/placeholders | scientifique |
| `initialize_root_tank_capacity` | `(j, data, paramITK)` | public | wrapper | init reservoir racinaire | partielle/placeholders | scientifique |
| `initialize_delta_root_tank_capacity` | `(j, data)` | public | wrapper | croissance capacite racinaire | bonne base | scientifique |
| `update_delta_root_tank_capacity` | `(j, data)` | public | wrapper | limite front humectation | partielle/placeholders | scientifique |
| `update_root_tank_capacity` | `(j, data)` | public | wrapper | maj capacite racinaire | partielle/placeholders | scientifique |
| `update_root_tank_stock` | `(j, data)` | public | wrapper | maj stock racinaire | partielle/placeholders | scientifique tres eleve |
| `EvolRurCstr2` | `(j, data, paramITK)` | public | loop | wrapper croissance racines | partielle | scientifique tres eleve |
| `update_previous_humectation_front_at_end_of_season` | `(j, data)` | public | non observe | memoire multi-cycle | partielle/placeholders | legacy |
| `update_humectation_front_at_end_of_season` | `(j, data)` | public | non observe | reset front humectation | partielle/placeholders | legacy |
| `update_root_tank_capacity_at_end_of_season` | `(j, data)` | public | non observe | memoire racines | partielle/placeholders | legacy |
| `update_previous_root_tank_stock_at_end_of_season` | `(j, data)` | public | non observe | memoire stock racines | partielle/placeholders | legacy |
| `update_previous_total_tank_stock_at_end_of_season` | `(j, data)` | public | non observe | memoire stock total | partielle/placeholders | legacy |
| `reset_total_tank_capacity` | `(j, data)` | public | wrapper | capacite sol totale | partielle/placeholders | moyen |
| `update_surface_tank_stock` | `(j, data)` | public | wrapper | remplissage surface | partielle/placeholders | scientifique |
| `estimate_transpirable_water` | `(j, data)` | public | wrapper | eau transpirable | partielle/placeholders | scientifique |
| `update_total_tank_stock` | `(j, data)` | public | wrapper | stock total | partielle/placeholders | scientifique |
| `update_delta_total_tank_stock` | `(j, data)` | public | non observe | delta stock total | partielle/placeholders | legacy |
| `update_total_tank_stock_for_second_crop_cycle` | `(j, data)` | public | non observe | multi-cycle | partielle/placeholders | legacy/fort |
| `update_previous_total_tank_stock_for_second_crop_cycle` | `(j, data)` | public | non observe | multi-cycle | partielle/placeholders | legacy/fort |
| `update_delta_total_tank_stock_step_2` | `(j, data)` | public | non observe | multi-cycle | partielle/placeholders | legacy/fort |
| `apply_humectation_front_boundaries` | `(j, data)` | public | wrapper | bornage front humectation | partielle/placeholders | scientifique |
| `update_drainage` | `(j, data)` | public | wrapper | drainage excedent | partielle/placeholders | scientifique |
| `update_total_tank_stock_after_drainage` | `(j, data)` | public | wrapper | stock apres drainage | partielle/placeholders | scientifique |
| `update_humectation_front_after_drainage` | `(j, data)` | public | wrapper | front apres drainage | partielle/placeholders | scientifique |
| `compute_drainage` | `(j, data)` | public | wrapper | wrapper drainage | partielle/placeholders | scientifique |
| `update_root_tank_stock_step_2` | `(j, data)` | public | wrapper | remplissage reservoir racinaire | partielle/placeholders | scientifique |
| `fill_tanks` | `(j, data)` | public | loop | wrapper reservoirs | partielle | scientifique eleve |
| `estimate_fesw` | `(j, data)` | public | wrapper | fraction eau evaporante | partielle/placeholders | scientifique |
| `estimate_kce` | `(j, data, paramITK)` | public | wrapper | coefficient evaporation sol | partielle/placeholders | scientifique |
| `estimate_soil_potential_evaporation` | `(j, data)` | public | wrapper | evaporation potentielle sol | partielle/placeholders | scientifique |
| `estimate_soil_evaporation` | `(j, data)` | public | wrapper | evaporation effective sol | partielle/placeholders | scientifique |
| `compute_soil_evaporation` | `(j, data, paramITK)` | public | loop | wrapper evaporation | absente | scientifique |
| `estimate_FEMcW_and_update_mulch_water_stock` | `(j, data, paramITK)` | public | loop | evaporation mulch | partielle/placeholders | scientifique |
| `estimate_ftsw` | `(j, data)` | public | wrapper | fraction eau transpirable | partielle/placeholders | scientifique |
| `estimate_potential_plant_transpiration` | `(j, data)` | public | wrapper | transpiration potentielle | partielle/placeholders | scientifique |
| `estimate_pFact` | `(j, data, paramVariete)` | public | wrapper | p factor FAO | partielle/placeholders | scientifique |
| `estimate_cstr` | `(j, data)` | public | wrapper | stress hydrique Ks-like | partielle/placeholders | scientifique |
| `estimate_plant_transpiration` | `(j, data)` | public | wrapper | transpiration reelle | partielle/placeholders | scientifique |
| `compute_transpiration` | `(j, data, paramVariete)` | public | loop | wrapper transpiration | absente | scientifique |
| `set_evapotranspirable_surface_water` | `(j, data)` | public | wrapper | snapshot surface | partielle/placeholders | moyen |
| `subtract_evap_from_surface_tank_stock` | `(j, data)` | public | wrapper | consommation evaporation surface | partielle/placeholders | moyen |
| `estimate_effective_evaporation_from_evaporable_water` | `(j, data)` | public | wrapper | evaporation effective | partielle/placeholders | scientifique |
| `subtract_effective_evaporation_from_total_tank_stock` | `(j, data)` | public | wrapper | consommation totale evap | partielle/placeholders | moyen |
| `update_effective_evaporation_for_shallow_roots` | `(j, data)` | public | wrapper | correction racines peu profondes | partielle/placeholders | scientifique |
| `subtract_effective_evaporation_from_root_tank_stock` | `(j, data)` | public | wrapper | consommation racinaire evap | partielle/placeholders | moyen |
| `update_plant_transpiration` | `(j, data)` | public | wrapper | borne transpiration par stock | partielle/placeholders | scientifique tres eleve |
| `subtract_transpiration_from_surface_tank_stock_according_to_root_tank_stock` | `(j, data)` | public | wrapper | repartition transpiration surface | partielle/placeholders | scientifique |
| `subtract_transpiration_from_root_tank_stock` | `(j, data)` | public | wrapper | conso racinaire transpiration | partielle/placeholders | moyen |
| `subtract_transpiration_from_total_tank_stock` | `(j, data)` | public | wrapper | conso totale transpiration | partielle/placeholders | moyen |
| `ConsoResSep` | `(j, data)` | public | loop | wrapper consommation eau | partielle | scientifique eleve |

Observations:

- Le module hydrique contient les doutes scientifiques les plus explicites dans
  les commentaires existants.
- `update_root_tank_stock` et `update_plant_transpiration` sont les deux points
  les plus sensibles: les commentaires internes indiquent deja une suspicion de
  creation/suppression d'eau ou de borne non intuitive.
- Les fonctions multi-cycle sont conservees mais commentees comme simplifiees ou
  non utilisees dans la boucle active.
- Plusieurs fonctions wrappers appelees par la boucle n'ont pas de docstring:
  `compute_soil_evaporation`, `compute_transpiration`.

### `sarra_py.bilan_carbo`

| Fonction | Signature | Visibilite | Appels | Role | Doc | Risque |
|---|---|---|---|---|---|---|
| `variable_dict` | `()` | public | init | metadonnees variables | vague | moyen |
| `initialize_simulation` | `(data, grid_width, grid_height, duration, paramVariete, paramITK, date_start)` | public | notebook | allocation et initialisation | partielle/placeholders | API/scientifique |
| `estimate_kcp` | `(j, data, paramVariete)` | public | hydro wrapper | coefficient transpiration plante | partielle | scientifique |
| `estimate_ltr` | `(j, data, paramVariete)` | public | loop | Beer-Lambert couverture | partielle | scientifique |
| `estimate_KAssim` | `(j, data, paramVariete)` | public | loop | facteur assimilation par phase | partielle | scientifique |
| `estimate_conv` | `(j, data, paramVariete)` | public | loop | conversion assimilats | vague | scientifique |
| `BiomDensOptSarraV4` | `(j, data, paramITK)` | public | non observe | legacy densite | partielle | legacy |
| `compute_rapDensite` | `(paramITK, paramVariete)` | public | init | correction densite | partielle/placeholders | scientifique |
| `adjust_for_sowing_density` | `(j, data, paramVariete, direction)` | public | loop | correction densite in/out | partielle/placeholders | scientifique |
| `EvalAssimSarrahV4` | `(j, data)` | public | non observe | legacy assim commente | vague | legacy |
| `update_assimPot` | `(j, data, paramVariete, paramITK)` | public | loop | assimilation potentielle | partielle | scientifique |
| `update_assim` | `(j, data)` | public | loop | assimilation sous stress hydrique | partielle/placeholders | scientifique |
| `calculate_maintainance_respiration` | `(j, data, paramVariete)` | public | loop | respiration maintenance | partielle | scientifique |
| `update_total_biomass` | `(j, data, paramVariete, paramITK)` | public | loop | biomasse totale | bonne base | scientifique |
| `update_total_biomass_stade_ip` | `(j, data)` | public | loop | biomasse initiation paniculaire | partielle | scientifique |
| `update_total_biomass_at_flowering_stage` | `(j, data)` | public | loop | biomasse floraison | partielle/placeholders | scientifique |
| `update_potential_yield` | `(j, data, paramVariete)` | public | loop | rendement potentiel | partielle | scientifique |
| `update_potential_yield_delta` | `(j, data, paramVariete)` | public | loop | demande journaliere rendement | bonne base | scientifique |
| `update_aboveground_biomass` | `(j, data, paramVariete)` | public | loop | biomasse aerienne | partielle | scientifique |
| `estimate_reallocation` | `(j, data, paramVariete)` | public | loop | reallocation feuilles/tiges vers grains | partielle | scientifique |
| `update_root_biomass` | `(j, data)` | public | loop | biomasse racinaire | partielle | scientifique |
| `update_leaf_biomass` | `(j, data, paramVariete)` | public | wrapper | biomasse feuilles si delta negatif | partielle/placeholders | scientifique |
| `update_stem_biomass` | `(j, data, paramVariete)` | public | wrapper | biomasse tige si delta negatif | partielle/placeholders | scientifique |
| `condition_positive_delta_biomass` | `(j, data, paramVariete)` | public | wrapper | condition allocation | absente | scientifique |
| `update_bM_and_cM` | `(j, data, paramVariete)` | public | wrapper | coefficients allometrie feuilles | partielle/placeholders | scientifique |
| `update_leaf_biomass_positive_delta_aboveground_biomass` | `(j, data, paramVariete)` | public | wrapper | feuilles delta positif | partielle/placeholders | scientifique |
| `update_stem_biomass_positive_delta_aboveground_biomass` | `(j, data, paramVariete)` | public | wrapper | tiges delta positif | partielle/placeholders | scientifique |
| `condition_positive_delta_aboveground_biomass_all_phases` | `(j, data)` | public | wrapper | condition reallocation | absente | scientifique |
| `update_leaf_biomass_all_phases` | `(j, data, paramVariete)` | public | wrapper | reallocation feuilles | partielle/placeholders | scientifique |
| `update_stem_biomass_all_phases` | `(j, data, paramVariete)` | public | wrapper | reallocation tiges | partielle/placeholders | scientifique |
| `update_aboveground_biomass_step_2` | `(j, data)` | public | wrapper | recomposition aerienne | partielle/placeholders | scientifique |
| `EvalFeuilleTigeSarrahV4` | `(j, data, paramVariete)` | public | loop | wrapper partition feuille/tige | partielle/placeholders | scientifique |
| `update_vegetative_biomass` | `(j, data)` | public | loop | tige + feuille | partielle/placeholders | scientifique |
| `calculate_canopy_specific_leaf_area` | `(j, data, paramVariete)` | public | loop | SLA canopee | bonne base | scientifique |
| `calculate_leaf_area_index` | `(j, data)` | public | loop | LAI | partielle | scientifique |
| `update_yield_during_filling_phase` | `(j, data)` | public | loop | remplissage grain | partielle | scientifique |
| `BiomDensiteSarraV42` | `(j, data, paramITK, paramVariete)` | public | non observe | legacy densite | absente | legacy |
| `BiomMcUBTSV3` | `(j, data, paramITK)` | public | non observe | decomposition mulch/UBT | vague | legacy |
| `MAJBiomMcSV3` | `(data)` | public | non observe | legacy recolte mulch | vague | legacy |
| `estimate_critical_nitrogen_concentration` | `(j, data)` | public | loop | courbe dilution azote | absente | scientifique |

Observations:

- `initialize_simulation` est longue et melange allocation, metadonnees,
  initialisation hydrique, initialisation carbone et calcul PAR.
- `variable_dict` est central pour les sorties, mais certaines unites ou
  `long_name` sont vides ou ambigues.
- Plusieurs fonctions legacy sont publiques, non appelees et parfois
  essentiellement commentees.
- `estimate_critical_nitrogen_concentration` est scientifiquement referencee en
  commentaire, appelee par la boucle, mais sans docstring et sans gestion du cas
  biomasse nulle.

## Fonctions sans docstring

Fonctions publiques sans docstring:

- `bilan_carbo.condition_positive_delta_biomass`
- `bilan_carbo.condition_positive_delta_aboveground_biomass_all_phases`
- `bilan_carbo.BiomDensiteSarraV42`
- `bilan_carbo.estimate_critical_nitrogen_concentration`
- `bilan_hydro.compute_soil_evaporation`
- `bilan_hydro.compute_transpiration`
- `bilan_pheno.reset`
- `data_preparation.initialize_default_irrigation`
- `data_preparation.calc_day_length_raster_fast`

Fonctions internes sans docstring:

- `bilan_pheno._to_numpy`
- `data_preparation._normalize_day_length_date`
- `data_preparation._cached_day_length_matrix`
- `data_preparation._broadcast_day_length_to_rain`
- toutes les fonctions internes de `models.py`

## Fonctions avec docstring insuffisante

Priorite elevee:

- `run_model`, `run_waterbalance_model`: ne documentent pas `engine`, `progress`,
  les dimensions attendues, les effets de bord, ni la preservation des sorties.
- `initialize_simulation`: ne liste pas les variables creees, les unites, les
  dimensions ni les effets de bord, malgre son role central.
- `calc_day_length_raster_fast`: absente alors que fonction publique notebook.
- `calculate_once_daily_thermal_time`: docstring conserve le doute `Pb de
  methode !?` sans expliciter l'equation active.
- `estimate_pFact`, `estimate_cstr`, `estimate_plant_transpiration`,
  `ConsoResSep`, `EvolRurCstr2`: docstrings riches mais avec placeholders et
  points non valides.
- `estimate_critical_nitrogen_concentration`: absence critique.

## Fonctions scientifiques critiques

Critiques par impact sur `rdt`, `cstr`, biomasse ou phenologie:

- Phenologie: `EvalPhenoSarrahV3`, `calculate_once_daily_thermal_time`,
  `calculate_sum_of_thermal_time`, `update_photoperiodism`,
  `MortaliteSarraV3`.
- Hydrique: `EvolRurCstr2`, `fill_tanks`, `compute_soil_evaporation`,
  `compute_transpiration`, `ConsoResSep`, `estimate_pFact`, `estimate_cstr`,
  `update_root_tank_stock`, `update_plant_transpiration`.
- Carbone/rendement: `estimate_ltr`, `estimate_KAssim`, `update_assimPot`,
  `update_assim`, `calculate_maintainance_respiration`,
  `update_total_biomass`, `update_potential_yield`,
  `update_potential_yield_delta`, `EvalFeuilleTigeSarrahV4`,
  `calculate_canopy_specific_leaf_area`,
  `update_yield_during_filling_phase`,
  `estimate_critical_nitrogen_concentration`.

## Choses etranges ou insuffisamment justifiees

Code observe:

- `update_root_tank_stock` contient deja un commentaire indiquant que la fonction
  est "probably wrong"; elle peut incrementer `root_tank_stock` avec
  `delta_root_tank_capacity`, ce qui melange capacite racinaire et stock d'eau.
- `update_plant_transpiration` met `tr` a `max(root_tank_stock - tr, 0)` lorsque
  `tr > root_tank_stock`; le commentaire propose que borner `tr` par
  `root_tank_stock` serait plus logique. Cette fonction peut donc annuler la
  transpiration dans un cas ou une borne par stock serait attendue.
- Les fonctions multi-cycle hydriques sont conservees mais desactivees dans
  `fill_tanks`; leur statut scientifique et API n'est pas clair.
- `estimate_transpirable_water` documente une ancienne correction 10%, puis la
  court-circuite avec `eauTranspi = available_water`.
- `estimate_fesw` documente encore un denominateur `1.1 *
  surface_tank_capacity`, mais le code utilise `surface_tank_capacity`.
- `update_surface_tank_stock` documente encore 110% de capacite, mais le code
  borne a 100%.
- `load_YAML_parameters` modifie `paramVariete["txConversion"]` si `NI` est non
  NaN; `update_assimPot` refait aussi cette modification. Effet de bord non
  documente et potentiellement duplique.
- `~np.isnan(value)` est utilise sur des scalaires pour tester la presence de
  parametres. C'est numeriquement equivalent dans beaucoup de cas, mais peu
  lisible et fragile si le type change.
- `initialize_simulation` cree des tableaux `(duration, grid_width,
  grid_height)` tout en assignant `data["rain"].dims`; cela suppose que
  `grid_width/grid_height` sont passes dans le meme ordre que les dimensions
  spatiales du dataset. Les notebooks semblent passer `grid_width =
  data.sizes["y"]`, `grid_height = data.sizes["x"]`, mais le nommage est source
  d'erreur.
- `variable_dict` contient plusieurs variables avec unite ou description vide:
  `kcTot`, `trSurf`, `conv`, `KAssim`, `FeuilleUp`, `kRespMaint`, `LitFeuille`,
  `nbJourCompte`, `nbjStress`, `NbUBT`, `sla`, `stockRac`, `sumPP`, `TigeUp`,
  `UBTCulture`, `Ncrit`.
- `load_paramVariete` contient une exception non documentee lorsque
  `feuilAeroBase == 0.1`.
- Les fonctions de chargement sol et YAML utilisent des chemins relatifs
  `../data/...`, dependants du repertoire courant.

Interpretation:

- Les plus grands risques de regression scientifique ne sont pas dans le moteur
  NumPy lui-meme, mais dans les formalismes hydriques historiques et leurs
  corrections partielles documentees en commentaires.
- La surface API publique est trop large: beaucoup de fonctions de bas niveau
  sont importables alors qu'elles devraient probablement rester internes ou
  legacy documentees.
- Les docstrings scientifiques contiennent une connaissance utile, mais pas dans
  un format exploitable par les utilisateurs notebook ou par de futurs tests.

## Fonctions couteuses ou mal structurees

Sans nouvelle optimisation appliquee, les zones a profiler en priorite sont:

- `initialize_simulation`: allocations nombreuses, `np.full`, `np.repeat`,
  creation de nombreuses variables xarray.
- `load_AgERA5_data`, `load_TAMSAT_data`: concat dans boucle et reprojections.
- `load_iSDA_soil_data*`: reprojections raster et mapping Python liste sur
  `soil_type.to_numpy().flatten()`.
- Boucle journaliere: ecritures `data["var"][j:,:,:]` et `np.where/xr.where`
  nombreuses, deja partiellement traitees par le moteur NumPy.
- `calculate_canopy_specific_leaf_area`: plusieurs divisions pouvant produire
  NaN/inf lorsque `biomasseFeuille == 0`; la condition masque partiellement mais
  `np.where` evalue les deux branches.
- `estimate_critical_nitrogen_concentration`: puissance negative sur biomasse
  nulle, warnings attendus.

## Recommandation API

Ne pas changer maintenant l'API notebook. A moyen terme:

1. definir explicitement `__all__` pour geler l'API publique reelle;
2. garder les fonctions notebook stables;
3. marquer les fonctions legacy non appelees comme "experimental/legacy" dans la
   documentation avant toute deprecation;
4. documenter les effets de bord de toutes les fonctions qui mutent `data`.
