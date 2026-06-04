# Audit des formalismes scientifiques de SARRA-Py

Date d'audit: 2026-06-04

## Principe de lecture

Ce document distingue trois niveaux:

- **Code observe**: ce qui est effectivement implemente dans `src/sarra_py`.
- **Source externe**: reference bibliographique ou documentation externe
  consultee.
- **Interpretation**: analyse de coherence ou risque; ne doit pas etre lue comme
  validation scientifique.

Aucune docstring scientifique et aucun formalisme n'ont ete modifies pendant cet
audit.

## Sources externes consultees

- FAO-56, Allen, Pereira, Raes & Smith (1998), *Crop evapotranspiration -
  Guidelines for computing crop water requirements*, table des matieres et
  chapitre 8 sur le stress hydrique:
  https://www.fao.org/3/X0490E/x0490e00.htm et
  https://www.fao.org/3/x0490e/x0490e0e.htm
- Dingkuhn, Kouressy, Vaksmann, Clerget & Chantereau (2008), modele
  "Impatience" du photoperiodisme du sorgho, notice CIRAD:
  https://publications.cirad.fr/une_notice.php?dk=543204
- Justes et al. (1994), *Determination of a Critical Nitrogen Dilution Curve for
  Winter Wheat Crops*, DOI `10.1006/anbo.1994.1133`:
  https://academic.oup.com/aob/article/74/4/397/2769191
- Leenaars et al. (2018), rootable depth and plant-available water holding
  capacity in sub-Saharan Africa, DOI `10.1016/j.geoderma.2018.02.046`:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5913732/
- iSDAsoil 30 m Africa soil properties, Scientific Reports:
  https://www.nature.com/articles/s41598-021-85639-y

Les sources externes confirment des familles de formalismes. Elles ne valident
pas automatiquement les variantes exactes implementees dans SARRA-Py.

## Conventions globales observees

### Dimensions et grille

Code observe:

- Les variables dynamiques sont stockees dans un `xarray.Dataset`.
- Les notebooks recents utilisent typiquement les dimensions `("time", "y",
  "x")`.
- Beaucoup de fonctions indexent directement `data["var"][j,:,:]` et ecrivent
  `data["var"][j:,:,:]`; cela suppose implicitement que la premiere dimension
  est temporelle et que les deux dimensions suivantes sont spatiales.
- `initialize_simulation` construit souvent des tableaux de forme `(duration,
  grid_width, grid_height)` et les assigne avec `data["rain"].dims`.

Interpretation:

- La convention temporelle journaliere est centrale mais insuffisamment
  documentee.
- Les noms `grid_width` et `grid_height` peuvent etre inverses par rapport aux
  dimensions `y/x`; les tests actuels devraient couvrir les dimensions et
  coordonnees pour eviter un retournement silencieux.

### Effets de bord

Code observe:

- Presque toutes les fonctions scientifiques mutent `data` en place et retournent
  le meme objet.
- Les fonctions propagent souvent la valeur courante sur tous les jours futurs
  avec `j:,:,:`.
- Les fonctions parametres peuvent muter `paramVariete`, notamment
  `load_YAML_parameters` et `update_assimPot` avec `txConversion` si `NI` est
  defini.

Interpretation:

- Les effets de bord sont une partie du formalisme numerique. Ils doivent etre
  documentes avant tout refactor.

## Formalismes phenologiques

### Initialisation et transitions de phases

Fonctions: `testing_for_initialization`, `flag_change_phase`,
`update_thermal_time_next_phase`, `increment_phase_number`,
`update_thermal_time_previous_phase`, `EvalPhenoSarrahV3`.

Code observe:

- `numPhase` va de 0 a 7.
- Phase 0: pas de culture ou apres recolte.
- Phase 1: conditions favorables a la germination jusqu'a levee.
- Phase 2: levee vers debut phase photoperiodique.
- Phase 3: phase photoperiodique.
- Phase 4: phase reproductive.
- Phase 5: debut maturation / remplissage grain.
- Phase 6: fin maturation.
- Phase 7: recolte.
- Initialisation quand `numPhase == 0`, `j >= sowing_date` et
  `surface_tank_stock >= seuilEauSemis`.
- Les transitions thermiques utilisent `sdj >= seuilTempPhaseSuivante`.
- Les seuils utilises sont notamment `SDJLevee`, `SDJBVP`, `SDJRPR`,
  `SDJMatu1`, `SDJMatu2`.

Unites attendues:

- `sdj`, `ddj`, seuils thermiques: degres-jours.
- `sowing_date`: index relatif en jours depuis `date_start`.

Risques:

- Transitions ecrites sur `j:`; tout changement d'ordre dans la boucle peut
  modifier le comportement futur.
- Les fonctions elementaires sont publiques mais ne sont pas concues comme API
  utilisateur.
- La docstring principale est riche, mais les petites fonctions manquent
  d'unites et de variables modifiees.

### Temps thermique journalier

Fonctions: `calculate_daily_thermal_time`, `calculate_once_daily_thermal_time`.

Code observe:

```text
if tpMoy <= TOpt2:
    ddj = max(min(TOpt1, tpMoy), TBase) - TBase
else:
    ddj = (TOpt1 - TBase)
          * (1 - ((min(TLim, tpMoy) - TOpt2) / (TLim - TOpt2)))
```

Le code actif utilise `tpMoy`, pas `TMin/TMax`, alors que la docstring conserve
une formule historique plus detaillee basee sur `TMin/TMax`.

Unites attendues:

- `tpMoy`, `TBase`, `TOpt1`, `TOpt2`, `TLim`: deg C.
- `ddj`: degres-jours par jour.

Points non verifies:

- La docstring mentionne explicitement `Pb de methode !?`.
- Il faut valider si la formule moyenne journaliere est la version scientifique
  souhaitee ou une simplification temporaire.

Risque:

- Eleve: impact direct sur phenologie, stress, rendement et duree de phase.

### Photoperiodisme

Fonctions: `calc_day_length`, `calc_day_length_raster_fast`,
`update_photoperiodism`.

Code observe:

- `calc_day_length` utilise `astral.sun.daylight` avec longitude fixee a 0 et
  latitude du pixel.
- `calc_day_length_raster_fast` produit `dureeDuJour` en heures sur les
  dimensions de `rain`.
- `update_photoperiodism` calcule:

```text
thermal_time_since_previous_phase = max(0.01, sdj - seuilTempPhasePrec)
time_above_critical_day_length = max(0, dureeDuJour - PPCrit)

sumPP = 100                 if numPhase == 3 and changePhase == 1
sumPP = (1000 / thermal_time_since_previous_phase) ** PPExp
        * time_above_critical_day_length / (SeuilPP - PPCrit)
                            if numPhase == 3 otherwise

phasePhotoper = 0 if numPhase == 3 and sumPP < PPsens
```

Source externe:

- Dingkuhn et al. (2008) developpent un modele photoperiodique "Impatience" pour
  le sorgho fonde sur une baisse des exigences de longueur du jour pendant la
  phase photoperiodique.

Interpretation:

- Le code correspond a l'esprit d'une reponse photoperiodique de type
  impatience, mais la formule exacte `sumPP` et les parametres `PPExp`,
  `PPsens`, `PPCrit`, `SeuilPP` doivent rester valides par expertise SARRA.
- Longitude 0 affecte l'heure solaire mais la duree jour/nuit depend surtout de
  la latitude et de la date; cela devrait etre documente.

Risques:

- Division par `SeuilPP - PPCrit` sans garde explicite.
- `sumPP` est decrit comme variable quotidienne, pas cumul; ce point est
  important a documenter.

## Formalismes hydriques

### Reservoirs et bilan hydrique general

Fonctions: `fill_tanks`, `EvolRurCstr2`, `ConsoResSep`.

Code observe:

- Le modele represente au moins trois reservoirs:
  `surface_tank_stock`, `total_tank_stock`, `root_tank_stock`, avec capacites
  associees.
- Bilan journalier conceptuel:

```text
stock(d+1) = stock(d) + rain + irrigation
             - runoff - drainage - evaporation - transpiration
```

- Les reservoirs se recouvrent; le code manipule des hauteurs d'eau plutot que
  des profondeurs physiques independantes.

Interpretation:

- La documentation existante `docs/model_formalisms.md` est coherente avec cette
  lecture, mais les fonctions elementaires contiennent des exceptions et
  simplifications qui doivent etre documentees.

### Irrigation automatique

Fonctions: `compute_irrigation_state`, `update_irrigation_tank_stock`,
`update_irrigation_tank_capacity`, `compute_daily_irrigation`.

Code observe:

- Active seulement si `paramITK["irrigAuto"] == True`.
- Conditions: `numPhase > 0`, `numPhase < 6`, stock/capacite irrigation sous
  `irrigAutoTarget`.
- Dose:

```text
irrigTotDay = irrigation
              + min(max(((capacity - stock) * 0.9) - irrigation, 0), maxIrrig)
```

Risques:

- Les docstrings disent que la logique n'est pas encore validee en SARRA-Py.
- Division stock/capacite sans garde explicite si capacite nulle.
- Usage notebook observe surtout en conditions pluviales; couverture test
  irrigation a renforcer avant usage scientifique.

### Mulch et interception

Fonctions: `fill_mulch`, `compute_water_captured_by_mulch`,
`estimate_FEMcW_and_update_mulch_water_stock`.

Code observe:

```text
water_captured_by_mulch =
    min(
        available_water * (1 - exp(-surfMc / 1000 * biomMc)),
        humSatMc * biomMc / 10000 - mulch_water_stock
    )

FEMcW = mulch_water_stock / (humSatMc * biomMc / 1000)
mulch_water_stock =
    max(0, mulch_water_stock - ltr * ET0 * FEMcW**2)
```

Unites attendues:

- `available_water`, `mulch_water_stock`, `water_captured_by_mulch`: mm.
- `biomMc`: kg/ha.
- `surfMc`: ha/t ou couverture rapportee a kg via `/1000`.
- `humSatMc`: kg eau/kg biomasse.

Risques:

- Les conversions `/1000` et `/10000` sont expliquees partiellement mais pas
  normalisees.
- Division par `biomMc` possible; warnings observes dans les tests lorsque
  `biomMc == 0`.
- Les docstrings indiquent que la logique mulch n'est pas pleinement validee.

### Ruissellement

Fonctions: `estimate_runoff`, `compute_runoff`.

Code observe:

```text
if rain > runoff_threshold:
    runoff = (available_water - runoff_threshold) * runoff_rate
else:
    runoff = 0
available_water -= runoff
```

Unites attendues:

- `rain`, `available_water`, `runoff_threshold`, `runoff`: mm.
- `runoff_rate`: fraction, convertie depuis pourcentage dans les helpers sol.

Questions:

- La condition utilise `rain`, mais le calcul utilise `available_water` apres
  irrigation/mulch. Cela peut etre voulu, mais doit etre explicite.
- La docstring demande deja si l'effet mulch devrait intervenir dans la condition
  de ruissellement.

### Croissance racinaire, front d'humectation et reservoirs

Fonctions: `initialize_delta_root_tank_capacity`,
`update_delta_root_tank_capacity`, `update_root_tank_capacity`,
`update_root_tank_stock`, `EvolRurCstr2`.

Code observe:

```text
delta_root_tank_capacity =
    vRac / 1000 * ru

if root_tank_capacity > surface_tank_capacity:
    delta_root_tank_capacity =
        vRac * min(cstr + 0.3, 1.0) / 1000 * ru

delta_root_tank_capacity =
    min(delta_root_tank_capacity, humectation_front - root_tank_capacity)

root_tank_capacity += delta_root_tank_capacity
```

Puis `update_root_tank_stock` fait notamment:

```text
if root_tank_capacity > surface_tank_capacity:
    root_tank_stock += delta_root_tank_capacity
else:
    root_tank_stock =
        max((surface_tank_stock - surface_tank_capacity * 0.1)
            * root_tank_capacity / surface_tank_capacity, 0)
```

Interpretation:

- La modulation `min(cstr + 0.3, 1)` traduit une tolerance de croissance
  racinaire au stress hydrique.
- Le code melange ensuite une variation de capacite racinaire et un stock d'eau.
  Les commentaires internes signalent deja ce point comme probablement incorrect.

Risque:

- Tres eleve. Ne pas changer sans validation scientifique et tests de bilan de
  masse.

### FESW, evaporation sol, Kce

Fonctions: `estimate_fesw`, `estimate_kce`,
`estimate_soil_potential_evaporation`, `estimate_soil_evaporation`.

Code observe:

```text
fesw = surface_tank_stock / surface_tank_capacity
kce = ltr * mulch * exp(-coefMc * surfMc * biomMc / 1000)
evapPot = ET0 * kce
evap = min(evapPot * fesw**2, surface_tank_stock)
```

Source externe:

- Le code cite Alhassane et compare le formalisme a FAO-56. FAO-56 distingue le
  coefficient d'evaporation du sol `Ke` et les effets de stress sur transpiration
  via `Ks`.

Interpretation:

- `fesw**2` est une variante empirique, differente du coefficient `Kr` FAO-56.
- La docstring mentionne encore `110% surface_tank_capacity`, mais le code actif
  utilise 100%.

Risques:

- Division par capacite nulle.
- Incoherence doc/code sur 110%.
- Le formalisme n'est pas sol-specifique comme FAO-56 `TEW/REW`.

### FTSW, p factor, stress hydrique et transpiration

Fonctions: `estimate_ftsw`, `estimate_potential_plant_transpiration`,
`estimate_pFact`, `estimate_cstr`, `estimate_plant_transpiration`,
`compute_transpiration`.

Code observe:

```text
ftsw = root_tank_stock / root_tank_capacity if capacity > 0 else 0
trPot = kcp * ET0
pFact = PFactor + 0.04 * (5 - kcp * ET0)
pFact = min(max(pFact, 0.1), 0.8)
cstr = min(ftsw / (1 - pFact), 1)
cstr = max(cstr, 0)
tr = trPot * cstr
```

Source externe:

- FAO-56 chapitre 8 definit `TAW`, `RAW = p TAW`, et un coefficient de stress
  hydrique `Ks` compris entre 0 et 1. FAO-56 donne aussi l'ajustement usuel de
  `p` par la demande evaporative, borne entre 0.1 et 0.8.

Interpretation:

- `cstr` correspond a une forme `Ks` exprimee en remplissage (`ftsw`) plutot
  qu'en depletion (`Dr`). Si `ftsw >= 1 - p`, pas de stress.
- Le code abandonne une ancienne borne `max(kcp, 1)` dans `pFact`; le commentaire
  indique que cette borne n'etait pas justifiee.

Risques:

- Coherence plutot bonne avec FAO-56 pour l'esprit `p/Ks`, mais la variable
  `ETc` utilisee dans l'ajustement est ici `kcp * ET0` et non une formulation
  complete.
- A documenter clairement avant validation.

### Consommation d'eau et separation evaporation/transpiration

Fonctions: `ConsoResSep`, `set_evapotranspirable_surface_water`,
`subtract_evap_from_surface_tank_stock`,
`estimate_effective_evaporation_from_evaporable_water`,
`update_effective_evaporation_for_shallow_roots`,
`update_plant_transpiration`,
`subtract_transpiration_from_surface_tank_stock_according_to_root_tank_stock`,
`subtract_transpiration_from_root_tank_stock`,
`subtract_transpiration_from_total_tank_stock`.

Code observe:

- Evaporation retiree d'abord du reservoir de surface.
- `consoRur` borne l'evaporation par `trSurf`.
- Si racines peu profondes, `consoRur` est module par
  `root_tank_stock / surface_tank_capacity`.
- `tr` est ajuste si `tr > root_tank_stock` par:

```text
tr = max(root_tank_stock - tr, 0)
```

Interpretation:

- L'ordre des processus est justifie dans la docstring: evaporation consideree
  plus rapide et consommant d'abord la surface.
- Le recalcul de `tr` est probablement le point le plus suspect: une borne
  intuitive serait `min(tr, root_tank_stock)`, mais ce serait un changement
  scientifique et ne doit pas etre fait sans validation.

Risque:

- Tres eleve pour `update_plant_transpiration`.

## Formalismes carbone, biomasse et rendement

### Radiation, couverture et assimilation potentielle

Fonctions: `initialize_simulation`, `estimate_ltr`, `estimate_KAssim`,
`estimate_conv`, `update_assimPot`, `update_assim`.

Code observe:

```text
par = 0.5 * rg
ltr = exp(-kdf * lai)
KAssim = fonction de numPhase et parfois interpolation par sdj
conv = KAssim * txConversion
assimPot = par * (1 - exp(-kdf * lai)) * conv * 10
assim = assimPot * tr / trPot if trPot > 0 else 0
```

Unites attendues:

- `rg`: MJ/m2/j.
- `par`: MJ/m2/j.
- `assimPot`, `assim`: kg/ha/j selon variable metadata.
- `lai`: m2/m2.
- `kdf`: coefficient extinction.

Interpretation:

- Approche "big leaf" et Beer-Lambert coherente avec
  `docs/model_formalisms.md`.
- Constantes `0.5` pour PAR et `10` pour conversion MJ/m2 vers kg/ha-equivalent
  doivent etre documentees.
- `KAssim` phases 5 et 6 interpole par `sdj`; divisions possibles si seuils
  thermiques egaux.

### Intensification `NI`

Fonctions: `load_YAML_parameters`, `update_assimPot`.

Code observe:

```text
txConversion =
    NIYo + NIp * (1 - exp(-NIp * NI))
    - exp(-0.5 * ((NI - LGauss) / AGauss)**2)
      / (AGauss * 2.506628274631)
```

Risques:

- Formule non sourcee dans les docs.
- Mutation de `paramVariete`.
- Calculee a deux endroits.
- `AGauss == 0` non protege.

### Respiration de maintenance

Fonction: `calculate_maintainance_respiration`.

Code observe:

```text
coefficient_temp = 2 ** ((tpMoy - tempMaint) / 10)
respMaint = kRespMaint * biomasseTotale * coefficient_temp
            + kRespMaint * biomasseFeuille * coefficient_temp
```

Interpretation:

- Formalisme de type `Q10 = 2`.
- La biomasse foliaire est ajoutee en plus de la biomasse totale; si
  `biomasseTotale` inclut deja les feuilles, cela peut etre un choix de
  ponderation ou un double comptage. Validation requise.

### Biomasse totale et aerienne

Fonctions: `update_total_biomass`, `update_aboveground_biomass`,
`update_root_biomass`, `update_vegetative_biomass`.

Code observe:

- A levee, biomasse totale initialisee par densite, reserve grain et poids sec:

```text
biomasseTotale =
    densite * max(1, densOpti / densite) * txResGrain * poidsSecGrain / 1000
```

- Ensuite:

```text
deltaBiomasseTotale = assim - respMaint
biomasseTotale += deltaBiomasseTotale
biomasseAerienne =
    min(0.9, aeroTotPente * biomasseTotale + aeroTotBase) * biomasseTotale
    for phases 2..4
biomasseRacinaire = biomasseTotale - biomasseAerienne
```

Risques:

- `densOpti` NaN dans `update_total_biomass` n'est pas protege comme ailleurs.
- Plafond `0.9` non source.
- Biomasse peut devenir negative si `assim < respMaint` durablement; certaines
  fonctions bornent ensuite les organes, mais pas toutes les variables.

### Densite de semis

Fonctions: `compute_rapDensite`, `adjust_for_sowing_density`.

Code observe:

```text
rapDensite =
    densiteA + densiteP
    * exp(-(densite / (densOpti / -log((1 - densiteA) / densiteP))))
```

`adjust_for_sowing_density` multiplie les biomasses et le rendement par
`rapDensite` en entree de bilan carbone, puis divise en sortie.

Risques:

- Equation qualifiee dans la docstring de probablement trop complexe.
- Conditions de validite sur `densiteA`, `densiteP`, `densOpti` absentes.
- La correction `in/out` est fragile: tout ajout de variable carbone doit savoir
  s'il doit etre corrige.

### Rendement potentiel et remplissage

Fonctions: `update_total_biomass_stade_ip`,
`update_total_biomass_at_flowering_stage`, `update_potential_yield`,
`update_potential_yield_delta`, `estimate_reallocation`,
`update_yield_during_filling_phase`.

Code observe:

```text
rdtPot =
    KRdtPotA * (biomTotStadeFloraison - biomTotStadeIp)
    + KRdtPotB
    + KRdtBiom * biomTotStadeFloraison

if phaseDevVeg < 6:
    rdtPot <= 2 * biomasseTige

dRdtPot =
    max(
        rdtPot * (ddj / SDJMatu1) * (tr / trPot),
        respMaint * 0.15
    )

manqueAssim = max(0, dRdtPot - max(0, deltaBiomasseAerienne))
reallocation = min(manqueAssim * txRealloc, max(0, biomasseFeuille - 30))
rdt += min(dRdtPot, max(0, deltaBiomasseAerienne) + reallocation)
```

Risques:

- Seuil feuille `30`, minimum `respMaint * 0.15`, plafond `2 *
  biomasseTige`, coefficients `KRdt*` non references dans docs.
- Division par `trPot`; `np.where` evalue les deux branches, donc warnings
  possibles meme si la sortie est masquee.

### Partition feuilles/tiges, SLA et LAI

Fonctions: `EvalFeuilleTigeSarrahV4`, `update_bM_and_cM`,
`update_leaf_biomass*`, `update_stem_biomass*`,
`calculate_canopy_specific_leaf_area`, `calculate_leaf_area_index`.

Code observe:

- Si delta aerien negatif: diminution feuilles/tiges selon reallocation.
- Si delta positif: coefficients `bM`, `cM` et relation exponentielle:

```text
bM = feuilAeroBase - 0.1
cM = ((feuilAeroPente * 1000) / bM + 0.78) / 0.75
biomasseFeuille =
    (0.1 + bM * cM ** ((biomasseAerienne - rdt) / 1000))
    * (biomasseAerienne - rdt)
```

- SLA:

```text
ratio_old = biomasseFeuille[j-1] / biomasseFeuille[j]
ratio_new = deltaBiomasseFeuilles[j] / biomasseFeuille[j]
sla_decrease = slaPente * (sla - slaMin)
sla = weighted old/new SLA
sla = min(slaMax, max(slaMin, sla))
lai = biomasseFeuille * sla for phases 2..6
```

Risques:

- Division par biomasse foliaire nulle; warnings observes.
- Plancher organes `1e-8` non documente comme seuil numerique.
- `condition_positive_delta_biomass` utilise
  `(numPhase <= 4) | (numPhase <= phaseDevVeg)`, ce qui est equivalent a une
  condition large; demander si `|` est bien voulu.
- La docstring de SLA est longue et utile, mais contient des doublons et des
  placeholders.

### Mortalite juvenile

Fonction: `MortaliteSarraV3`.

Code observe:

- Compte les jours depuis emergence (`nbJourCompte`).
- Compte les jours de stress si `deltaBiomasseAerienne < 0` pendant les
  `nbjTestSemis` premiers jours.
- Si `nbjStress == seuilCstrMortality`, met `numPhase`, `root_tank_capacity` et
  `nbjStress` a 0.

Risques:

- La docstring dit que le formalisme semble simpliste.
- Le test final utilise `== seuilCstrMortality`, pas `>=`; si le compteur saute
  une valeur, la mortalite peut ne pas se declencher.

### Azote critique

Fonction: `estimate_critical_nitrogen_concentration`.

Code observe:

```text
Ncrit = 5.35 * (biomasseTotale / 1000) ** (-0.44)
```

Source externe:

- Justes et al. (1994) donnent pour ble d'hiver une courbe
  `Nct = 5.35 DM^-0.442` pour une biomasse aerienne entre environ 1.55 et
  12 t/ha.

Interpretation:

- Le coefficient et l'exposant correspondent a l'ordre de grandeur de Justes et
  al.
- Le code utilise `biomasseTotale / 1000`, donc une biomasse en kg/ha convertie
  en t/ha.

Risques:

- La source concerne le ble d'hiver et la biomasse aerienne; le code utilise
  `biomasseTotale`, dans un modele cultures tropicales. Cela necessite validation
  scientifique.
- Pas de garde pour biomasse nulle; warnings `divide by zero` observes.
- Pas de docstring.

## Formalismes sol et donnees externes

Fonctions: `load_iSDA_soil_data`, `load_iSDA_soil_data_alternate`.

Code observe:

- `profRu`: profondeur racinaire/sol issue d'un raster Africa SoilGrids/RZD,
  convertie de cm vers mm par `* 10`.
- `RZPAWC`: root zone plant available water capacity en mm.
- `ru = RZPAWC / (profRu / 1000)`, donc `ru` en mm/m.
- `runoff_threshold` et `runoff_rate` derives de classes iSDA/HWSD; le
  pourcentage de ruissellement est divise par 100.

Sources externes:

- Leenaars et al. (2018) documentent rootable depth et root zone plant-available
  water holding capacity en Afrique subsaharienne.
- iSDAsoil documente des proprietes de sol africaines a 30 m.

Risques:

- Les chemins de donnees sont codes en dur.
- La correspondance classe texture -> proprietes hydriques est locale au CSV et
  doit etre documentee comme source scientifique separee.
- Les dimensions `grid_width/grid_height` sont utilisees dans `np.reshape` et
  doivent correspondre exactement a l'ordre spatial du dataset.

## Points non verifies

- Source exacte des coefficients SARRA-H historiques pour rendement,
  reallocation, SLA, densite et intensification `NI`.
- Validite par espece des parametres photoperiodiques (`PPsens`, `PPExp`,
  `SeuilPP`, `PPCrit`).
- Validite de l'application Justes et al. a `biomasseTotale` et aux cultures
  ciblees par SARRA-Py.
- Statut scientifique des fonctions hydriques marquees comme douteuses dans les
  commentaires.
- Role exact des fonctions multi-cycle desactivees.
- Convention precise de l'unite de `txConversion`, `conv`, `KAssim` et du
  facteur `* 10` dans `assimPot`.

## Questions necessitant validation scientifique

1. `calculate_once_daily_thermal_time`: la formule active basee sur `tpMoy` est-
   elle la reference souhaitee, ou faut-il revenir a une formule `TMin/TMax`?
2. `update_root_tank_stock`: le stock racinaire doit-il vraiment augmenter avec
   `delta_root_tank_capacity`?
3. `update_plant_transpiration`: lorsque `tr > root_tank_stock`, faut-il garder
   `max(root_tank_stock - tr, 0)` ou borner par `root_tank_stock`?
4. `estimate_fesw` et `update_surface_tank_stock`: la capacite surface doit-elle
   etre 100% ou 110%?
5. `estimate_critical_nitrogen_concentration`: doit-on utiliser biomasse totale,
   aerienne, ou des courbes specifiques a la culture?
6. Les fonctions multi-cycle doivent-elles etre supportees, documentees comme
   legacy, ou depreciees?
7. Les corrections de densite `adjust_for_sowing_density` doivent-elles couvrir
   d'autres variables carbone nouvellement ajoutees?
