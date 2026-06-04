import numpy as np
import xarray as xr

def variable_dict():
    """
    Retrieve the dictionary of variables in the dataset with their respective units.

    Returns:
        dict: A dictionary containing the variables and their units, where the keys are the variable names and the values are the respective units.

    """   

    variables = {
        # climate
        "ddj": ["daily thermal time", "°C.j"],
        "sdj": ["sum of thermal time since beginning of emergence", "°C.j"],

        # phenology
        "changePhase": ["indicator of phase transition day", "binary"],
        "numPhase": ["number of phenological stage", "arbitrary units"],
        "initPhase": ["indicator of performed phase transition", "binary"],
        "phasePhotoper": ["photoperiodic phase indicator", "binary"],
        "seuilTempPhaseSuivante": ["sum of thermal time needed to reach the next phenological phase", "°C.j"],
        "sommeDegresJourPhasePrec": ["sum of thermal time needed to reach the previous phenological phase", "°C.j"],
        "seuilTempPhasePrec": ["sum of thermal time needed to reach the previous phenological phase", "°C.j"],


        # carbon balance
        "assim": ["plant biomass assimilation", "kg/ha"],
        "assimPot": ["plant potential biomass assimilation", "kg/ha"],
        "bM": ["net growth rate of living biomass", "kg/(m².d)"],
        "cM": ["net growth rate of dead biomass", "kg/(m².d)"],
        "rdt": ["grain yield", "kg/ha"],
        "rdtPot": ["potential grain yield", "kg/ha"],
        "reallocation": ["amount of assimilates reallocated to the yield (supply < demand)", "kg/ha"],
        "respMaint": ["amount of assimilates consumed by maintainance respiration", "kg/ha"],
        "manqueAssim": ["deficit in assimilates (demand - supply)", "kg/ha"],


        # biomass
        "biomTotStadeFloraison": ["total biomass of the plant at the end of the flowering stage", "kg/ha"],
        "biomTotStadeIp": ["total biomass at the panicle initiation stage", "kg/ha"],
        "deltaBiomasseAerienne": ["increment of aerial biomass in one day", "kg/(ha.d)"],
        "deltaBiomasseFeuilles": ["increment of leaf biomass in one day", "kg/(ha.d)"],
        "biomasseAerienne": ["total aerial biomass", "kg/ha"],
        "biomasseVegetative": ["total vegetative biomass", "kg/ha"],
        "biomasseTotale": ["total biomass", "kg/ha"],
        "biomasseTige": ["total stem biomass", "kg/ha"],
        "biomasseRacinaire": ["total root biomass", "kg/ha"],
        "biomasseFeuille": ["total leaf biomass", "kg/ha"],
        "deltaBiomasseTotale": ["increment of total biomass in one day", "kg/(ha.d)"],

        # evapotranspiration
        "kce": ["fraction of kc attributable to soil evaporation","decimal percentage"],
        "kcp": ["fraction of kc attributable to plant transpiration","decimal percentage"],
        "kcTot": ["total crop coefficient",""],
        "tr": ["actual crop transpiration","mm/d"],
        "trPot": ["potential crop transpiration","mm/d"],
        "trSurf": ["",""],

        # water balance
        "consoRur": ["consumption of water stored in the root system", "mm"],
        "water_captured_by_mulch" : ["water captured by the mulch in one day","mm"],
        "available_water" : ["available water, sum of rainfall and total irrigation for the day","mm"],
        "eauTranspi": ["water available for transpiration from the surface reservoir","mm"],
        "correctedIrrigation" : ["corrected irrigation amount","mm/d"],
        "cstr" : ["drought stress coefficient", "arbitrary unit"],
        "dayVrac" : ["modulated daily root growth","mm/day"],
        "delta_root_tank_capacity": ["change in root system water reserve","mm"],
        "drainage": ["drainage","mm"],
        #// "etm": ["evapotranspiration from the soil moisture","mm/d"],
        "etp": ["potential evapotranspiration from the soil moisture","mm/d"],
        #// "etr": ["reference evapotranspiration","mm/d"],
        "evap": ["evaporation from the soil moisture","mm/d"],
        "evapPot": ["potential evaporation from the soil moisture","mm/d"],
        "FEMcW": ["water fraction in soil volume explored by the root system","none"],
        "fesw": ["fraction of available surface water","decimal percentage"],
        "irrigTotDay" : ["total irrigation for the day","mm"],
        "vRac" : ["reference daily root growth","mm/day"],
        "ftsw": ["fraction of transpirable surface water","decimal percentage"], 
        "runoff" : ["daily water runoff","mm/d"],
        "pFact": ["FAO reference for critical FTSW value for transpiration response","none"],



        # water tanks
        "irrigation_tank_stock" : ["current stock of water in the irrigation tank","mm"], #! renaming stockIrr to irrigation_tank_stock
        "mulch_water_stock" : ["water stored in crop residues (mulch)","mm"], #! renaming stockMc to mulch_water_stock
        "root_tank_stock": ["current stock of water in the root system tank","mm"], #! renaming stRu to root_tank_stock
        "total_tank_capacity": ["total capacity of the root system tank","mm"], #! renaming stRuMax to total_tank_capacity
        "stRur": ["",""], # ["previous season's root system tank stock","mm"],
        "previous_root_tank_capacity": ["previous season's root system tank capacity","mm"], #! renaming stRurMaxPrec to previous_root_tank_capacity
        "previous_root_tank_stock": ["previous day's root system tank stock","mm"],
        "stRurSurf": ["surface root system tank stock","mm"],
        "surface_tank_stock": ["current stock of water in the surface root system tank","mm"], #! renaming stRuSurf to surface_tank_stock
        "stRuSurfPrec": ["previous day's surface root system tank stock","mm"],
        "delta_total_tank_stock": ["change in the total root system tank stock","mm"], #! renaming stRuVar to delta_total_tank_stock
        "irrigation_tank_capacity" : ["irrigation tank capacity","mm"], #! renaming ruIrr to irrigation_tank_capacity
        "ruRac": ["Water column that can potentially be strored in soil volume explored by root system","mm"],
        


        "conv": ["",""],
        "KAssim": ["",""],


        "dayBiomLeaf": ["daily growth of leaf biomass","kg/ha/d"],
        "dRdtPot": ["daily potential demand from yield","kg/ha/d"],
        "FeuilleUp": ["",""],
        
        
        "kRespMaint": ["",""],
        "LitFeuille": ["",""],
        
        
        "nbJourCompte": ["",""],
        "nbjStress": ["",""],
        "NbUBT": ["",""],
        
        
        "sla": ["",""],

        "stockRac": ["",""],
        "sumPP": ["",""],
        "TigeUp": ["",""],
        "UBTCulture": ["",""],
        "lai":["leaf area index","m2/m2"],

        # experimental
        "Ncrit": ["",""],
    }

    return variables





def initialize_simulation(data, grid_width, grid_height, duration, paramVariete, paramITK, date_start):
    """Initialize crop, water, carbon and output variables on the rainfall grid.

    Creates daily state variables with `data["rain"].dims`, sets default units
    and metadata where available, and mutates the input dataset in place.

    Source status: code-observed initialization, source-related to SARRA-H
    `InitiationCulture` and `InitPlotMc` procedure comments.
    """

    ### variables to be initialized with values from parameters 

    # from paramVariete : maximum daily thermal time (°C.j) -> #? unused ?
    #// data["sommeDegresJourMaximale"] = (data["rain"].dims, np.full(
    #//     (duration, grid_width, grid_height),
    #//     (paramVariete["SDJLevee"] + paramVariete["SDJBVP"] + paramVariete["SDJRPR"] + paramVariete["SDJMatu1"] + paramVariete["SDJMatu2"])
    #// ))
    #// data["sommeDegresJourMaximale"].attrs = {"units":"°C.j", "long_name":"Maximum thermal time"}

    # from paramITK : sowing date
    data["sowing_date"] = (data["rain"].dims, np.full((duration, grid_width, grid_height), (paramITK["DateSemis"] - date_start).days))
    
    # from paramITK : automatic irrigation indicator
    data["irrigAuto"] = (data["rain"].dims, np.full((duration, grid_width, grid_height), paramITK["irrigAuto"]))
    data["irrigAuto"].attrs = {"units":"binary", "long_name":"automatic irrigation indicator"}

    ####### variables qui viennent de initplotMc
    # Initial biomass of crop residues (mulch) (kg/ha)
    # Biomasse initiale des résidus de culture (mulch) (kg/ha)
    #   BiomMc := BiomIniMc;
    data["biomMc"] = (data["rain"].dims, np.full((duration, grid_width, grid_height), paramITK["biomIniMc"]))
    data["biomMc"].attrs = {"units": "kg/ha", "long_name": "Initial biomass of crop residues (mulch)"}
    data["biomMc"] = data["biomMc"].astype("float32")


    # ?
    #   StSurf := StockIniSurf;
    # data["stSurf"] = np.full((grid_width, grid_height, duration), paramTypeSol["stockIniSurf"])


    # ?
    #   Ltr := 1;
    data["ltr"] = (data["rain"].dims, np.full((duration, grid_width, grid_height), 1.0))
    data["ltr"] = data["ltr"].astype("float32")


    # Initial biomass of stem residues as litter (kg/ha)
    # Biomasse initiale des résidus de tiges sous forme de litière (kg/ha)
    #   LitTiges := BiomIniMc;
    data["LitTige"] = (data["rain"].dims, np.full((duration, grid_width, grid_height), paramITK["biomIniMc"]))
    data["LitTige"].attrs = {"units": "kg/ha", "long_name": "Initial biomass of stem residues as litter"}
    data["LitTige"] = data["LitTige"].astype("float32")

    ####### fin variables qui viennent de initplotMc

    ####### variables eau depuis InitPlotMc

    # Initializes variables related to crop residues boimass (mulch) in the data
    # xarray dataset. This code has been adapted from the original InitPlotMc
    # procedure, Bileau.pas code. Comments with tab indentation are from the
    # original code. As the rain is the first variable to be initialized in the
    # data xarray dataset, its dimensions are used to initialize the other
    # variables.

    # Soil maximum water storage capacity (mm)
    # Capacité maximale de la RU (mm)
    #   StRurMax := Ru * ProfRacIni / 1000;
    #! renaming stRurMax with root_tank_capacity
    #// data["stRurMax"] = data["ru"] * paramITK["profRacIni"] / 1000
    data["root_tank_capacity"] = (data["rain"].dims, np.repeat(np.array(data["ru"] * paramITK["profRacIni"] / 1000)[np.newaxis,:,:], duration, axis=0))
    #// data["stRurMax"].attrs = {"units": "mm", "long_name": "Soil maximum water storage capacity"}
    data["root_tank_capacity"].attrs = {"units": "mm", "long_name": "Soil maximum water storage capacity"}


    # Maximum water capacity of surface tank (mm)
    # Reserve utile de l'horizon de surface (mm)
    #   RuSurf := EpaisseurSurf / 1000 * Ru;
    #! renaming ruSurf with surface_tank_capacity
    #// data["ruSurf"] = data["epaisseurSurf"] / 1000 * data["ru"]
    data["surface_tank_capacity"] = data["epaisseurSurf"] / 1000 * data["ru"]
    #// data["ruSurf"].attrs = {"units": "mm", "long_name": "Maximum water capacity of surface tank"}
    data["surface_tank_capacity"].attrs = {"units": "mm", "long_name": "Maximum water capacity of surface tank"}
    

    # ?
    #   //    PfTranspi := EpaisseurSurf * HumPf;
    #   //    StTot := StockIniSurf - PfTranspi/2 + StockIniProf;
    #   StTot := StockIniSurf  + StockIniProf;
    # data["stTot"] = np.full((grid_width, grid_height, duration), (paramTypeSol["stockIniSurf"] + paramTypeSol["stockIniProf"]))
    #! modifié pour faire correspondre les résultats de simulation, à remettre en place pour un calcul correct dès que possible
    # data["stTot"] = np.full((grid_width, grid_height, duration), (paramTypeSol["stockIniProf"]))
    #! renaming stTot to total_tank_stock
    #// data["stTot"] = data["stockIniProf"]
    #//data["total_tank_stock"] = data["stockIniProf"]
    #! coorecting total_tank_stock initialization as it did not have the time dimensions that are required as stock evolves through time
    data["total_tank_stock"] = (data["rain"].dims, np.repeat(np.array(data["stockIniProf"])[np.newaxis,:,:], duration, axis=0))
    #// data["stTot"].attrs = {"units": "mm", "long_name": "?"}
    data["total_tank_stock"].attrs = {"units": "mm", "long_name": "?"}
    

    # Soil maximal depth (mm)
    # Profondeur maximale de sol (mm)
    #   ProfRU := EpaisseurSurf + EpaisseurProf;
    #! data["profRu"] = data["epaisseurProf"] + data["epaisseurSurf"]
    #! data["profRu"].attrs = {"units": "mm", "long_name": "Soil maximal depth"}
    # déplacé dans l'initialisation du sol

    # Maximum water capacity to humectation front (mm)
    # Quantité d'eau maximum jusqu'au front d'humectation (mm)
    #   // modif 10/06/2015  resilience stock d'eau
    #   // Front d'humectation egal a RuSurf trop de stress initial
    #   //    Hum := max(StTot, StRurMax);
    #   Hum := max(RuSurf, StRurMax);
    #   // Hum mis a profRuSurf
    #   Hum := max(StTot, Hum);
    data["humectation_front"] = (data["rain"].dims, np.full((duration, grid_width, grid_height),
        np.maximum(
            np.maximum(
                #! renaming ruSurf with surface_tank_capacity
                #// data["ruSurf"],
                data["surface_tank_capacity"].expand_dims({"time":duration}),
                #! renaming stRurMax with root_tank_capacity
                #// data["stRurMax"],
                data["root_tank_capacity"],
            ),
            #! renaming stTot with total_tank_stock
            #// data["stTot"],
            data["total_tank_stock"],
        )
    ))
    data["humectation_front"].attrs = {"units": "mm", "long_name": "Maximum water capacity to humectation front"}


    # Previous value for Maximum water capacity to humectation front (mm)
    #  HumPrec := Hum;
    data["previous_humectation_front"] = data["humectation_front"]
    
    
    # ?
    #   StRurPrec := 0;


    # Previous value for stTot
    #   StRurMaxPrec := 0;
    #   //modif 10/06/2015 resilience stock d'eau
    #! renaming stTot with total_tank_stock
    #! renaminog stRuPrec with previous_total_tank_stock
    #// data["stRuPrec"] =  data["stTot"]
    data["previous_total_tank_stock"] =  data["total_tank_stock"]

    ####### fin variables eau depuis InitPlotMc


    # depuis meteo.pas
    kpar = 0.5
    data["par"] = kpar * data["rg"]
    data["par"].attrs = {"units":"MJ/m2", "long_name":"par"}


    # crop density
    if ~np.isnan(paramVariete["densOpti"]) :
        data["rapDensite"] = data["rain"] * 0 + compute_rapDensite(paramITK, paramVariete)
        data["rapDensite"].attrs = {"units":"none", "long_name":"sowing density adjustement factor"}

    # initialize variables with values at 0
    variables = variable_dict()

    for variable in variables :
        data[variable] = (data["rain"].dims, np.zeros(shape=(duration, grid_width, grid_height)))
        data[variable].attrs = {"units":variables[variable][1], "long_name":variables[variable][0]}
        data[variable] = data[variable].astype("float32")

    return data


    


def estimate_kcp(j, data, paramVariete):
    """
    Estimate the kcp coefficient based on the maximum crop coefficient `kcMax` and plant cover `ltr`.

    The computation of `kcp` is based on the EvolKcpKcIni procedure from the biomasse.pas and exmodules 1 & 2.pas files of the original PASCAL code.

    Args:
        j (int): The starting index for updating `kcp` in the `data` dataset.
        data (xarray.Dataset): A dataset containing the data used in the computation of `kcp`. The dataset should contain the following variables:
            - 'numPhase': A 3-dimensional data variable with shape (num_timesteps, num_rows, num_columns), representing the number of phases in the crop cycle.
            - 'kcp': A 3-dimensional data variable with shape (num_timesteps, num_rows, num_columns), representing the coefficient of crop growth.
            - 'ltr': A 3-dimensional data variable with shape (num_timesteps, num_rows, num_columns), representing the plant cover.
        paramVariete (dict): A dictionary containing the parameters for estimating `kcp`. The dictionary should contain the following key:
            - 'kcMax': A float, representing the maximum crop coefficient.

    Returns:
        xarray.Dataset: The updated `data` dataset with the new `kcp` values.
    """

    data["kcp"][j:,:,:] = np.where(
        data["numPhase"][j,:,:] >= 1,
        np.maximum(0.3, paramVariete["kcMax"] * (1 - data["ltr"][j,:,:])),
        data["kcp"][j,:,:],
    )
    
    return data




def estimate_ltr(j, data, paramVariete):
    """Estimate the fraction of radiation transmitted through the canopy.

    ``ltr = exp(-kdf * lai)``

    `lai` is leaf area index and `kdf` is the canopy extinction coefficient.
    Values near 1 indicate little canopy interception.

    Source status: source-related to Beer-Lambert canopy interception.
    """
    # group 80   
    data["ltr"][j:,:,:] = np.exp(-paramVariete["kdf"] * data["lai"][j,:,:])
    
    return data




def estimate_KAssim(j, data, paramVariete):
    """Estimate the phase-dependent assimilation coefficient.

    Phases 2-4 use fixed values; phases 5-6 linearly interpolate between
    maturity coefficients using accumulated degree-days. Equal phase thresholds
    can produce division warnings.

    Source status: code-observed.
    """

    phase_equivalences = {
        2: 1,
        3: paramVariete['txAssimBVP'],
        4: paramVariete['txAssimBVP'],
        #! replacing sommeDegresJourPhasePrec with seuilTempPhasePrec
        #// 5: paramVariete["txAssimBVP"] + (data['sdj'][j,:,:] - data['sommeDegresJourPhasePrec'][j,:,:]) * (paramVariete['txAssimMatu1'] -  paramVariete['txAssimBVP']) / (data['seuilTempPhaseSuivante'][j,:,:] - data['sommeDegresJourPhasePrec'][j,:,:]),
        5: paramVariete["txAssimBVP"] + (data['sdj'][j,:,:] - data['seuilTempPhasePrec'][j,:,:]) * (paramVariete['txAssimMatu1'] -  paramVariete['txAssimBVP']) / (data['seuilTempPhaseSuivante'][j,:,:] - data['seuilTempPhasePrec'][j,:,:]),
        #// 6: paramVariete["txAssimMatu1"] + (data["sdj"][j,:,:] - data["sommeDegresJourPhasePrec"][j,:,:]) * (paramVariete["txAssimMatu2"] - paramVariete["txAssimMatu1"]) / (data["seuilTempPhaseSuivante"][j,:,:] - data["sommeDegresJourPhasePrec"][j,:,:]),
        6: paramVariete["txAssimMatu1"] + (data["sdj"][j,:,:] - data["seuilTempPhasePrec"][j,:,:]) * (paramVariete["txAssimMatu2"] - paramVariete["txAssimMatu1"]) / (data["seuilTempPhaseSuivante"][j,:,:] - data["seuilTempPhasePrec"][j,:,:]),
    }

    for phase in range(2,7):
        data["KAssim"][j:,:,:] = np.where(
            data["numPhase"][j,:,:] == phase,
            phase_equivalences[phase],
            data["KAssim"][j,:,:],
        )

    return data



def estimate_conv(j,data,paramVariete):
    """Update the biomass conversion coefficient used for assimilation.

    ``conv = KAssim * txConversion``

    The downstream `update_assimPot` equation applies an additional factor 10;
    the exact unit convention remains documented in `model_formalisms.md`.

    Source status: code-observed.
    """
    data["conv"][j:,:,:] = (data["KAssim"][j,:,:] * paramVariete["txConversion"])

    return data




def BiomDensOptSarraV4(j, data, paramITK):
    """
    si densité plus faible alors on considére qu'il faut augmenter les biomasses, LAI etc
    en regard de cette situation au niveau de chaque plante (car tout est rapporté é des kg/ha).
    Si elle est plus forte on ne change rien pour lors.
    Valeur fixe en ref au maés é déf en paramétre par variétésé rapDensite := Max(1, 70000/densite);

    """
    """
    if ~np.isnan(paramVariete["densOpti"]) :
        paramITK["rapDensite"] = np.maximum(1,paramVariete["densOpti"]/paramITK["densite"])
        data["rdt"][j,:,:] = data["rdt"][j,:,:] * paramITK["rapDensite"]
        data["biomasseRacinaire"][j,:,:] = data["biomasseRacinaire"][j,:,:] * paramITK["rapDensite"]
        data["biomasseTige"][j,:,:] = data["biomasseTige"][j,:,:] * paramITK["rapDensite"]
        data["biomasseFeuille"][j,:,:] = data["biomasseFeuille"][j,:,:] * paramITK["rapDensite"]
        data["biomasseAerienne"][j,:,:] = data["biomasseTige"][j,:,:] + data["biomasseFeuille"][j,:,:] + data["rdt"][j,:,:] 
        data["lai"][j,:,:]  = data["biomasseFeuille"][j,:,:] * data["sla"][j,:,:]
        data["biomasseTotale"][j,:,:] = data["biomasseAerienne"][j,:,:] + data["biomasseRacinaire"][j,:,:]

    return data
    """
    return data




def compute_rapDensite(paramITK, paramVariete):
    """
    It basically calculates a correction factor (rapDensite).
    This correction factor Is calculated with an equation of form

    a + p * exp( -(x/(o / -log((1-a)/p) )) )

    with a the densiteA parameter
    p the densiteP parameter$
    x the actual crop density
    o the densOpti parameter

    See
    https://www.wolframalpha.com/input?i=a+%2B+p+*+exp%28-%28x+%2F+%28+o%2F-+log%28%281+-+a%29%2F+p%29%29%29%29
    for equation visualization.

    This equation is probably too complex for the problem at hand.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramITK (_type_): _description_
        paramVariete (_type_): _description_

    Returns:
        _type_: _description_
    """

    rapDensite = paramVariete["densiteA"] + paramVariete["densiteP"] * np.exp(-(paramITK["densite"] / ( paramVariete["densOpti"]/- np.log((1 - paramVariete['densiteA'])/ paramVariete["densiteP"]))))
    return rapDensite




def adjust_for_sowing_density(j, data, paramVariete, direction):
    """
    This function translates the effect of sowing density on biomass and LAI.

    This function is adapted from the BiomDensOptSarV42 and BiomDensiteSarraV42
    procedures, from the bilancarbonsarra.pas original Pascal code.

    Notes from CB : 
    if density is lower than the optimal density, then we consider that we need
    to increase the biomass, LAI etc in regard of this situation at each plant
    level (because everything is related to kg/ha). If it is higher, it
    increases asymptotically.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramITK (_type_): _description_
        paramVariete (_type_): _description_

    Returns:
        _type_: _description_
    """
    if direction == "in" :
        if ~np.isnan(paramVariete["densOpti"]) :
            
            data["rdt"][j:,:,:] = data["rdt"][j,:,:] * data["rapDensite"][j,:,:]
            data["rdtPot"][j:,:,:] = (data["rdtPot"][j,:,:] * data["rapDensite"][j,:,:])
            data["biomasseRacinaire"][j:,:,:] = (data["biomasseRacinaire"][j,:,:] * data["rapDensite"][j,:,:])
            data["biomasseTige"][j:,:,:] = (data["biomasseTige"][j,:,:] * data["rapDensite"][j,:,:])
            data["biomasseFeuille"][j:,:,:] = (data["biomasseFeuille"][j,:,:] * data["rapDensite"][j,:,:])
            data["biomasseAerienne"][j:,:,:] = (data["biomasseTige"][j,:,:] + data["biomasseFeuille"][j,:,:] + data["rdt"][j,:,:])
            data["lai"][j:,:,:]  = (data["biomasseFeuille"][j,:,:] * data["sla"][j,:,:])
            data["biomasseTotale"][j:,:,:] = (data["biomasseAerienne"][j,:,:] + data["biomasseRacinaire"][j,:,:])
        
        return data
    
    if direction == "out":
        if ~np.isnan(paramVariete["densOpti"]):

            data["rdt"][j:,:,:] = (data["rdt"][j,:,:] / data["rapDensite"][j,:,:])
            data["rdtPot"][j:,:,:] = (data["rdtPot"][j,:,:]/ data["rapDensite"][j,:,:])
            data["biomasseRacinaire"][j:,:,:] = (data["biomasseRacinaire"][j,:,:] / data["rapDensite"][j,:,:])
            data["biomasseTige"][j:,:,:] = (data["biomasseTige"][j,:,:] / data["rapDensite"][j,:,:])
            data["biomasseFeuille"][j:,:,:] = (data["biomasseFeuille"][j,:,:] / data["rapDensite"][j,:,:])
            data["biomasseAerienne"][j:,:,:] = (data["biomasseTige"][j,:,:] + data["biomasseFeuille"][j,:,:] + data["rdt"][j,:,:])
            #? conflit avec fonction evolLAIphase ?
            #data["lai"][j:,:,:]  = data["biomasseFeuille"][j,:,:] * data["sla"][j,:,:]
            data["lai"][j:,:,:]  = data["lai"][j:,:,:]  / data["rapDensite"][j,:,:]
            data["biomasseTotale"][j:,:,:] = (data["biomasseAerienne"][j,:,:] + data["biomasseRacinaire"][j,:,:])#[...,np.newaxis]
            #data["biomasseTotale"][j:,:,:] = data["biomasseTotale"][j:,:,:] / data["rapDensite"]

        return data




def EvalAssimSarrahV4(j, data):
    """
    data["parIntercepte"][j,:,:] = 0.5 * (1 - data["ltr"][j,:,:]) * data["rg"][j,:,:]
    data["assimPot"][j:,:,:] = data["parIntercepte"][j,:,:] * data["conv"][j,:,:] * 10

    data["assim"][j,:,:] = np.where(
        data["trPot"][j,:,:] > 0,
        data["assimPot"][j,:,:] * data["tr"][j,:,:] / data["trPot"][j,:,:],
        0,
    )
    """
    return data
    

def update_assimPot(j, data, paramVariete, paramITK):
    """Compute potential assimilation from PAR, canopy interception and conversion.

    ``assimPot = par * (1 - exp(-kdf * lai)) * conversion * 10``

    `par` is expected in MJ m-2 day-1. If `NI` is defined, the current code
    recomputes and mutates `paramVariete["txConversion"]`; that NI formalism
    remains an open validation point.

    Source status: source-related to big-leaf/RUE modelling; conversion factors
    and NI response are code-observed.
    """
    if ~np.isnan(paramITK["NI"]): 
        #? the following (stupidly long) line was found commented, need to check why and if this is correct
        
        paramVariete["txConversion"] = paramVariete["NIYo"] + paramVariete["NIp"] * (1-np.exp(-paramVariete["NIp"] * paramITK["NI"])) - (np.exp(-0.5*((paramITK["NI"] - paramVariete["LGauss"])/paramVariete["AGauss"])* (paramITK["NI"]- paramVariete["LGauss"])/paramVariete["AGauss"]))/(paramVariete["AGauss"]*2.506628274631)
        # NIYo + NIp * (1-exp(-NIp * NI)) - (exp(-0.5*((NI - LGauss)/AGauss)* (NI- LGauss)/AGauss))/(AGauss*2.506628274631)
        data["assimPot"][j,:,:] = data["par"][j,:,:] * \
            (1-np.exp(-paramVariete["kdf"] * data["lai"][j,:,:])) * \
            paramVariete["txConversion"] * 10
    else :
        data["assimPot"][j,:,:] = data["par"][j,:,:] * \
            (1-np.exp(-paramVariete["kdf"] * data["lai"][j,:,:])) * \
            data["conv"][j,:,:] * 10
    
    return data





def update_assim(j, data):
    """Apply transpiration stress to potential assimilation.

    ``assim = assimPot * tr / trPot`` where ``trPot > 0``; otherwise ``assim``
    is set to 0.

    Source status: code-observed stress scaling.
    """

    data["assim"][j,:,:] = np.where(
        data["trPot"][j,:,:] > 0,
        data["assimPot"][j,:,:] * data["tr"][j,:,:] / data["trPot"][j,:,:],
        0,
    )

    return data




def calculate_maintainance_respiration(j, data, paramVariete):
    """Compute maintenance respiration for the current day.

    Uses a Q10-like coefficient `2 ** ((tpMoy - tempMaint) / 10)` and applies
    it to total biomass plus leaf biomass. The extra leaf term remains a
    validation question if total biomass already includes leaves.

    Source status: source-related to Q10 respiration; biomass pool choice is
    code-observed.
    """
    coefficient_temp = 2**((data["tpMoy"][j,:,:] - paramVariete["tempMaint"]) / 10)
    resp_totale = paramVariete["kRespMaint"] * data["biomasseTotale"][j,:,:] * coefficient_temp
    resp_feuille = paramVariete["kRespMaint"] * data["biomasseFeuille"][j,:,:] * coefficient_temp

    data["respMaint"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] > 4) & (data["biomasseFeuille"][j,:,:]==0),
        0,
        resp_totale + resp_feuille,
    )

    return data




def update_total_biomass(j, data, paramVariete, paramITK):
    """Update total crop biomass and its daily increment.

    At emergence it initializes biomass from density and seed reserves.
    Otherwise `biomasseTotale += assim - respMaint` and
    `deltaBiomasseTotale = assim - respMaint`.

    Source status: code-observed, source-related to SARRA-H biomass procedure
    comments.
    """

    data["biomasseTotale"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:]==2) & (data["changePhase"][j,:,:]==1),
        paramITK["densite"] *  np.maximum(1,paramVariete['densOpti']/paramITK['densite']) * paramVariete["txResGrain"] *  paramVariete["poidsSecGrain"] / 1000,
        data["biomasseTotale"][j,:,:]  + (data["assim"][j,:,:] - data["respMaint"][j,:,:]),
    )

    # we may want to drop this variable and use the raw computation instead
    data["deltaBiomasseTotale"][j:,:,:] = (data["assim"][j,:,:] - data["respMaint"][j,:,:])

    return data




def update_total_biomass_stade_ip(j, data):
    """Store total biomass at panicle-initiation stage.

    Saves `biomasseTotale` into `biomTotStadeIp` when phase 4 starts.

    Source status: code-observed.
    """
    data["biomTotStadeIp"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 4) & (data["changePhase"][j,:,:] == 1),
        data["biomasseTotale"][j,:,:],
        data["biomTotStadeIp"][j,:,:],
    )

    return data





def update_total_biomass_at_flowering_stage(j, data):
    """Store total biomass at flowering stage.

    Saves `biomasseTotale` into `biomTotStadeFloraison` when phase 5 starts.

    Source status: code-observed.
    """
    data["biomTotStadeFloraison"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 5) & (data["changePhase"][j,:,:] == 1),
        data["biomasseTotale"][j,:,:],
        data["biomTotStadeFloraison"][j,:,:],
    )

    return data





def update_potential_yield(j, data, paramVariete):
    """Initialize potential grain yield at the start of phase 5.

    ``delta = biomTotStadeFloraison - biomTotStadeIp``

    ``rdtPot = KRdtPotA * delta + KRdtPotB
    + KRdtBiom * biomTotStadeFloraison``

    Applies at phase-5 entry; for `phaseDevVeg < 6`, the result is capped at
    `2 * biomasseTige`. Coefficients remain calibration-sensitive.

    Source status: code-observed, not externally validated here.
    """

    delta_biomass_flowering_ip = data["biomTotStadeFloraison"][j,:,:] - data["biomTotStadeIp"][j,:,:]

    data["rdtPot"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 5) & (data["changePhase"][j,:,:] == 1),
        (paramVariete["KRdtPotA"] * delta_biomass_flowering_ip + paramVariete["KRdtPotB"]) + paramVariete["KRdtBiom"] * data["biomTotStadeFloraison"][j,:,:],
        data["rdtPot"][j,:,:],
    )

    #! phaseDevVeg pas utilisé ? attention c'est un paramètre variétal et pas un jeu de donées
    data["rdtPot"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 5) & (data["changePhase"][j,:,:] == 1) & (data["rdtPot"][j,:,:] > data["biomasseTige"][j,:,:] * 2) & (paramVariete["phaseDevVeg"] < 6),
        data["biomasseTige"][j,:,:] * 2,
        data["rdtPot"][j,:,:],
    )
    
    return data





def update_potential_yield_delta(j, data, paramVariete):
    """Update daily potential yield demand during grain filling.

    ``dRdtPot = max(rdtPot * (ddj / SDJMatu1) * (tr / trPot),
    respMaint * 0.15)`` where ``trPot > 0``.

    Applies during phase 5. `trPot == 0` gives 0, though NumPy may still emit
    masked division warnings.

    Source status: code-observed, not externally validated here.
    """
    data["dRdtPot"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 5),
        np.where(
            (data["trPot"][j,:,:] > 0),
            np.maximum(
                data["rdtPot"][j,:,:] * (data["ddj"][j,:,:] / paramVariete["SDJMatu1"]) * (data["tr"][j,:,:] / data["trPot"][j,:,:]),
                data["respMaint"][j,:,:] * 0.15,
            ),
            0,
        ),
        data["dRdtPot"][j,:,:],
    )

    return data





def update_aboveground_biomass(j, data, paramVariete):
    """Partition total biomass into aboveground biomass for the current day.

    ``biomasseAerienne = min(0.9, aeroTotPente * biomasseTotale
    + aeroTotBase) * biomasseTotale``

    This applies during phases 2-4. Other phases add `deltaBiomasseTotale`.
    The daily delta is `biomasseAerienne[j] - biomasseAerienne[j - 1]`.

    Source status: code-observed empirical partitioning.
    """
    #// data["deltaBiomasseAerienne"][j:,:,:] = np.copy(data["biomasseAerienne"][j,:,:])

    data["biomasseAerienne"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] >= 2) & (data["numPhase"][j,:,:] <= 4),
        np.minimum(0.9, paramVariete["aeroTotPente"] * data["biomasseTotale"][j,:,:] + paramVariete["aeroTotBase"]) * data["biomasseTotale"][j,:,:],
        data["biomasseAerienne"][j,:,:] + data["deltaBiomasseTotale"][j,:,:],
    )

    #//data["deltaBiomasseAerienne"][j:,:,:] = (data["biomasseAerienne"][j,:,:] - data["deltaBiomasseAerienne"][j,:,:])#[...,np.newaxis]
    
    data["deltaBiomasseAerienne"][j:,:,:] = data["biomasseAerienne"][j,:,:] - data["biomasseAerienne"][j-1,:,:]

    return data





def estimate_reallocation(j, data, paramVariete):
    """Estimate biomass reallocation toward grain filling.

    ``manqueAssim = max(0, dRdtPot - max(0, deltaBiomasseAerienne))``

    ``reallocation = min(manqueAssim * txRealloc,
    max(0, biomasseFeuille - 30))``

    Applies only during phase 5. The leaf reserve threshold `30` is an
    active-code constant still to be sourced.

    Source status: code-observed.
    """

    condition = (data["numPhase"][j,:,:] == 5)

    data["manqueAssim"][j:,:,:] = np.where(
        condition,
        np.maximum(0, (data["dRdtPot"][j,:,:] -  np.maximum(0.0, data["deltaBiomasseAerienne"][j,:,:]))),
        0,
    )

    data["reallocation"][j:,:,:] = np.where(
        condition,
        np.minimum(
            data["manqueAssim"][j,:,:] * paramVariete["txRealloc"], 
            np.maximum(0.0, data["biomasseFeuille"][j,:,:] - 30),
        ),
        0,
    )

    return data





def update_root_biomass(j, data):
    """Update root biomass as the residual of total and aboveground biomass.

    ``biomasseRacinaire = biomasseTotale - biomasseAerienne``

    Source status: code-observed.
    """
    data["biomasseRacinaire"][j,:,:] = data["biomasseTotale"][j,:,:] - data["biomasseAerienne"][j,:,:]

    return data





def update_leaf_biomass(j, data, paramVariete):
    """Update leaf biomass when aboveground biomass decreases.

    ``biomasseFeuille = max(1e-8, biomasseFeuille
    - (reallocation - deltaBiomasseAerienne) * pcReallocFeuille)``

    Applies where the crop is active and aboveground biomass decreases. The
    `1e-8` floor is a numerical guard, not a validated biological threshold.

    Source status: code-observed.
    """

    data["biomasseFeuille"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] > 1) & (data["deltaBiomasseAerienne"][j,:,:] < 0),
        np.maximum(
            0.00000001,
            data["biomasseFeuille"][j,:,:] - (data["reallocation"][j,:,:] - data["deltaBiomasseAerienne"][j,:,:]) * paramVariete["pcReallocFeuille"]
        ),
        data["biomasseFeuille"][j,:,:],
    )

    return data



def update_stem_biomass(j, data, paramVariete):
    """Update stem biomass when aboveground biomass decreases.

    ``biomasseTige = max(1e-8, biomasseTige
    - (reallocation - deltaBiomasseAerienne) * (1 - pcReallocFeuille))``

    Applies where the crop is active and aboveground biomass decreases. The
    `1e-8` floor is a numerical guard, not a validated biological threshold.

    Source status: code-observed.
    """
    # group 122
    data["biomasseTige"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] > 1) & (data["deltaBiomasseAerienne"][j,:,:] < 0),
        np.maximum(
            0.00000001,
            data["biomasseTige"][j,:,:] - (data["reallocation"][j,:,:] - data["deltaBiomasseAerienne"][j,:,:]) * (1 - paramVariete["pcReallocFeuille"]),
            ),
        data["biomasseTige"][j,:,:],
    )

    return data





def condition_positive_delta_biomass(j, data, paramVariete):
    """Return the mask for allometric leaf/stem partitioning.

    Mask: `numPhase > 1`, `deltaBiomasseAerienne >= 0`, and
    `(numPhase <= 4 or numPhase <= phaseDevVeg)`. The broad `or` condition is
    intentionally documented as current behaviour.

    Source status: code-observed.
    """


    condition = (data["numPhase"][j,:,:] > 1) & \
        (data["deltaBiomasseAerienne"][j,:,:] >= 0) & \
        ((data["numPhase"][j,:,:] <= 4) | (data["numPhase"][j,:,:] <= paramVariete["phaseDevVeg"]))
        # (data["numPhase"][j,:,:] <= 4)

    return condition


def update_bM_and_cM(j, data, paramVariete):
    """Update allometric coefficients for positive aboveground biomass growth.

    ``bM = feuilAeroBase - 0.1``

    ``cM = ((feuilAeroPente * 1000) / bM + 0.78) / 0.75``

    Used by positive-growth leaf/stem partitioning. `bM == 0` can produce
    division warnings.

    Source status: code-observed empirical allometry.
    """

    data["bM"][j,:,:] = np.where(
        condition_positive_delta_biomass(j, data, paramVariete),
        paramVariete["feuilAeroBase"] - 0.1,
        data["bM"][j,:,:],
    )


    data["cM"][j,:,:] = np.where(
        condition_positive_delta_biomass(j, data, paramVariete),
        ((paramVariete["feuilAeroPente"] * 1000)/ data["bM"][j,:,:] + 0.78) / 0.75,
        data["cM"][j,:,:],
    )

    return data


def update_leaf_biomass_positive_delta_aboveground_biomass(j, data, paramVariete):
    """Update leaf biomass from allometry when aboveground biomass increases.

    ``biomasseFeuille = (0.1 + bM * cM ** ((biomasseAerienne - rdt) / 1000))
    * (biomasseAerienne - rdt)``

    Applies only on the positive-growth partition mask. Coefficients remain
    empirical current-code constants.

    Source status: code-observed.
    """
    data["biomasseFeuille"][j:,:,:] = np.where(
        condition_positive_delta_biomass(j, data, paramVariete),
        (0.1 + data["bM"][j,:,:] * data["cM"][j,:,:] ** ((data["biomasseAerienne"][j,:,:] - data["rdt"][j,:,:]) / 1000)) \
            * (data["biomasseAerienne"][j,:,:] - data["rdt"][j,:,:]),
        data["biomasseFeuille"][j,:,:],
    )

    return data



def update_stem_biomass_positive_delta_aboveground_biomass(j, data, paramVariete):
    """Update stem biomass as the residual of aboveground organs.

    ``biomasseTige = biomasseAerienne - biomasseFeuille - rdt``

    Source status: code-observed.
    """
    data["biomasseTige"][j:,:,:] = np.where(
        condition_positive_delta_biomass(j, data, paramVariete),
        data["biomasseAerienne"][j,:,:] - data["biomasseFeuille"][j,:,:] - data["rdt"][j,:,:],
        data["biomasseTige"][j,:,:],
    )

    return data




def condition_positive_delta_aboveground_biomass_all_phases(j, data):
    """Return the mask for reallocation adjustments during positive growth.

    Mask: `numPhase > 1` and `deltaBiomasseAerienne > 0`.

    Source status: code-observed.
    """
    #// condition = (data["numPhase"][j,:,:] > 1) & (data["deltaBiomasseAerienne"][j,:,:] >= 0)
    condition = (data["numPhase"][j,:,:] > 1) & (data["deltaBiomasseAerienne"][j,:,:] > 0)
    return condition




def update_leaf_biomass_all_phases(j, data, paramVariete):
    """Subtract the leaf share of reallocation during positive growth.

    ``biomasseFeuille = biomasseFeuille - reallocation * pcReallocFeuille``

    Source status: code-observed.
    """

    data["biomasseFeuille"][j:,:,:] = np.where(
        condition_positive_delta_aboveground_biomass_all_phases(j, data),
        data["biomasseFeuille"][j,:,:] - data["reallocation"][j,:,:] * paramVariete["pcReallocFeuille"],
        data["biomasseFeuille"][j,:,:],
    )
    return data




def update_stem_biomass_all_phases(j, data, paramVariete):
    """Subtract the stem share of reallocation during positive growth.

    ``biomasseTige = biomasseTige - reallocation * (1 - pcReallocFeuille)``

    Source status: code-observed.
    """
    data["biomasseTige"][j:,:,:] = np.where(
        condition_positive_delta_aboveground_biomass_all_phases(j, data),
        data["biomasseTige"][j,:,:] - (data["reallocation"][j,:,:] * (1- paramVariete["pcReallocFeuille"])),
        data["biomasseTige"][j,:,:],
    )

    return data


def update_aboveground_biomass_step_2(j, data):
    """Recompose aboveground biomass from leaf, stem and grain biomass.

    ``biomasseAerienne = biomasseTige + biomasseFeuille + rdt``

    Source status: code-observed.
    """
    data["biomasseAerienne"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] > 1),
        data["biomasseTige"][j,:,:] + data["biomasseFeuille"][j,:,:] + data["rdt"][j,:,:],
        data["biomasseAerienne"][j,:,:],
    )
    return data

def EvalFeuilleTigeSarrahV4(j, data, paramVariete):
    """Update leaf and stem biomass partitioning for one day.

    Coordinates negative-growth reallocation, positive-growth allometry, leaf
    biomass delta, and recomposition of aboveground biomass. Several empirical
    coefficients remain documented centrally rather than in this wrapper.

    Source status: code-observed wrapper around empirical partitioning helpers.
    """

    # data["deltaBiomasseFeuilles"][j:,:,:] = np.where(
    #     (data["numPhase"][j,:,:] > 1),
    #     data["biomasseFeuille"][j,:,:],
    #     data["deltaBiomasseFeuilles"][j,:,:],
    # )

    # if (data["numPhase"][j,:,:] > 1) & (data["deltaBiomasseAerienne"][j,:,:] < 0)
    data = update_leaf_biomass(j, data, paramVariete)
    data = update_stem_biomass(j, data, paramVariete)

    # if deltaBiomasseAerienne >= 0 and (numPhase <= 4 or numPhase <= phaseDevVeg)
    data = update_bM_and_cM(j, data, paramVariete)
    data = update_leaf_biomass_positive_delta_aboveground_biomass(j, data, paramVariete)
    data = update_stem_biomass_positive_delta_aboveground_biomass(j, data, paramVariete)

    # if deltaBiomasseAerienne > 0 and numPhase > 1
    data = update_leaf_biomass_all_phases(j, data, paramVariete)
    data = update_stem_biomass_all_phases(j, data, paramVariete)

    # condition = (data["numPhase"][j,:,:] > 1) 
    # data["deltaBiomasseFeuilles"][j:,:,:] = np.where(
    #     (data["numPhase"][j,:,:] > 1),
    #     data["biomasseFeuille"][j,:,:] - data["deltaBiomasseFeuilles"][j,:,:],
    #     data["deltaBiomasseFeuilles"][j,:,:],
    # )

    # simpler formulation for updating the deltaBiomasseFeuilles
    data["deltaBiomasseFeuilles"][j:,:,:] = data["biomasseFeuille"][j,:,:] - data["biomasseFeuille"][j-1,:,:]

    data = update_aboveground_biomass_step_2(j, data)

    return data




def update_vegetative_biomass(j, data):
    """Update vegetative biomass from leaf and stem biomass.

    ``biomasseVegetative = biomasseTige + biomasseFeuille``

    Source status: code-observed.
    """
    data["biomasseVegetative"][j:,:,:] = (data["biomasseTige"][j,:,:] + data["biomasseFeuille"][j,:,:])
    return data




def calculate_canopy_specific_leaf_area(j, data, paramVariete):
    """Update canopy specific leaf area.

    At phase-2 entry, positive leaf biomass sets `sla = slaMax`.
    Afterwards, SLA decreases by `slaPente * (sla - slaMin)` and blends old
    and new leaf biomass contributions when leaf biomass grows.

    ``sla = (sla - sla_decrease) * ratio_old
    + ((slaMax + sla) / 2) * ratio_new``

    Values are clipped to `[slaMin, slaMax]`. Zero leaf biomass can still
    trigger masked division warnings.

    Source status: code-observed empirical SLA update.
    """

    condition = (data["biomasseFeuille"][j,:,:] > 0) & \
                (data["numPhase"][j,:,:] == 2) & \
                (data["changePhase"][j,:,:] == 1)

    data["sla"][j:,:,:] = np.where(
        condition,
        paramVariete["slaMax"],
        data["sla"][j,:,:],
    )

    ratio_old_leaf_biomass = data["biomasseFeuille"][j-1,:,:] / data["biomasseFeuille"][j,:,:]
    ratio_new_leaf_biomass = data["deltaBiomasseFeuilles"][j,:,:] / data["biomasseFeuille"][j,:,:]
    sla_decrease_step = paramVariete["slaPente"] * (data["sla"][j,:,:] - paramVariete["slaMin"])

    # Modif du 10/07/2018, DeltaBiomasse neg si reallocation ne pas fair l'evol du SLA dans ces conditions
    data["sla"][j:,:,:] = np.where(
        (data["biomasseFeuille"][j,:,:] > 0),
        np.where(
            (data["deltaBiomasseFeuilles"][j,:,:] > 0),
            #// (data["sla"][j,:,:] - paramVariete["slaPente"] * (data["sla"][j,:,:] - paramVariete["slaMin"])) * (data["biomasseFeuille"][j,:,:] - data["deltaBiomasseFeuilles"][j,:,:]) / data["biomasseFeuille"][j,:,:] + (paramVariete["slaMax"] + data["sla"][j,:,:])/2 * (data["deltaBiomasseFeuilles"][j,:,:] / data["biomasseFeuille"][j,:,:]),
            (data["sla"][j,:,:] - sla_decrease_step) * ratio_old_leaf_biomass + (paramVariete["slaMax"] + data["sla"][j,:,:])/2 * ratio_new_leaf_biomass,
            #//(data["sla"][j,:,:] - paramVariete["slaPente"] * (data["sla"][j,:,:] - paramVariete["slaMin"])) * (data["biomasseFeuille"][j,:,:] / data["biomasseFeuille"][j,:,:]),
            (data["sla"][j,:,:] - sla_decrease_step) * ratio_old_leaf_biomass,
        ),
        data["sla"][j,:,:],
    )

    data["sla"][j:,:,:] = np.where(
        (data["biomasseFeuille"][j,:,:] > 0),
        #// np.minimum(paramVariete["slaMin"], np.maximum(paramVariete["slaMax"], data["sla"][j,:,:])), # according to original
        # according to ocelet version
        np.minimum(
            paramVariete["slaMax"],
            np.maximum(
                paramVariete["slaMin"],
                data["sla"][j,:,:],
            ),
        ), 
        data["sla"][j,:,:],
    )

    return data





def calculate_leaf_area_index(j, data):
    """Update leaf area index from leaf biomass and SLA.

    Current rule: `lai = biomasseFeuille * sla` for phases 2-6, otherwise 0.

    Source status: code-observed, source-related to standard LAI definition.
    """

    data["lai"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] <= 1),
        0,
        np.where(
            data["numPhase"][j,:,:] <= 6,
            data["biomasseFeuille"][j,:,:] * data["sla"][j,:,:],
            0,
        )
    )

    return data





def update_yield_during_filling_phase(j, data):
    """Update grain yield during the filling phase.

    ``rdt = rdt + min(dRdtPot, max(0, deltaBiomasseAerienne)
    + reallocation)``

    Applies only during phase 5; outside phase 5, yield is unchanged.

    Source status: code-observed, not externally validated here.
    """

    data["rdt"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 5),
        data["rdt"][j,:,:] + np.minimum(data["dRdtPot"][j,:,:],  np.maximum(0.0, data["deltaBiomasseAerienne"][j,:,:]) + data['reallocation'][j,:,:]),
        data["rdt"][j,:,:],
    )

    return data




def BiomDensiteSarraV42(j, data, paramITK, paramVariete):
    # depuis bilancarbonsarra.pas
    
    if ~np.isnan(paramVariete["densOpti"]):

        data["rdt"][j:,:,:] = (data["rdt"][j,:,:] / data["rapDensite"])

        data["rdtPot"][j:,:,:] = (data["rdtPot"][j,:,:]/ data["rapDensite"])

        data["biomasseRacinaire"][j:,:,:] = (data["biomasseRacinaire"][j,:,:] / data["rapDensite"])

        data["biomasseTige"][j:,:,:] = (data["biomasseTige"][j,:,:] / data["rapDensite"])

        data["biomasseFeuille"][j:,:,:] = (data["biomasseFeuille"][j,:,:] / data["rapDensite"])

        data["biomasseAerienne"][j:,:,:] = (data["biomasseTige"][j,:,:] + data["biomasseFeuille"][j,:,:] + data["rdt"][j,:,:])

        #? conflit avec fonction evolLAIphase ?
        #data["lai"][j:,:,:]  = data["biomasseFeuille"][j,:,:] * data["sla"][j,:,:]
        data["lai"][j:,:,:]  = data["lai"][j:,:,:]  / data["rapDensite"]

        data["biomasseTotale"][j:,:,:] = (data["biomasseAerienne"][j,:,:] + data["biomasseRacinaire"][j,:,:])#[...,np.newaxis]
        #data["biomasseTotale"][j:,:,:] = data["biomasseTotale"][j:,:,:] / data["rapDensite"]

    return data





def BiomMcUBTSV3(j, data, paramITK):
    """
    depuis bilancarbonsarra.pas

    group 174

    Pendant la croissance des cultures la d�gradation des r�sidusest calcul�e sans les UBT
    Ici c'est pendant la saion s�che quand il n'y a des cultures pas de b�tes.
    Sur le mulch dress� (Up) ou couch� Lit), on calcul sa d�gradation journali�re
    sur les feuilles et les tiges en fn de coef KN (climat, termites...),
    KI ingestion par les b�tes pression en UBT seulement pour les feuilles, KT (effet pi�tinement) qui va faire passer
    du stade lev� en couch� et du stade couch� en ensevelissement pression en UBT
    Par D�faut :
    KNUp = 0.001 /jour
    KNLit = 0.011
    KN est soit une constante soit peut varier en fn climat (pas fait ref STEP)
    KT = 0.003
    KI = 0.005
    NbUBT = 10 (zone Fakara)
    """
    condition = (data["numPhase"][j,:,:] > 0)

    #   group 161
    data["UBTCulture"][j:,:,:] = np.where(condition, 0, data["NbUBT"][j,:,:])#[...,np.newaxis]
    #  group 162
    data["LitFeuille"][j:,:,:] = np.where(condition, data["LitFeuille"][j,:,:] + data["FeuilleUp"][j,:,:], data["LitFeuille"][j,:,:])#[...,np.newaxis]
    # group 163
    data["LitTige"][j:,:,:] = np.where(condition, data["LitTige"][j,:,:] + data["TigeUp"][j,:,:], data["LitTige"][j,:,:])#[...,np.newaxis]
    # group 164
    data["FeuilleUp"][j:,:,:] = np.where(condition, 0, data["FeuilleUp"][j,:,:])#[...,np.newaxis]
    # group 165
    data["TigeUp"][j:,:,:] = np.where(condition, 0, data["TigeUp"][j,:,:])#[...,np.newaxis]
    # group 166
    data["biomMc"][j:,:,:] = np.where(condition, data["LitFeuille"][j,:,:] + data["LitTige"][j,:,:], data["biomMc"][j,:,:])#[...,np.newaxis]

    #// D�gradation des feuilles et tiges dress�es
    # FeuilleUp := max(0, (FeuilleUp -  FeuilleUp * KNUp - FeuilleUp * KI * UBTCulture  - FeuilleUp * KT * UBTCulture));
    # group 167
    data["FeuilleUp"][j:,:,:] = np.maximum(
        0,
        data["FeuilleUp"][j,:,:] - data["FeuilleUp"][j,:,:] * paramITK["KNUp"] - data["FeuilleUp"][j,:,:] \
            * paramITK["KI"] * data["UBTCulture"][j,:,:] - data["FeuilleUp"][j,:,:] * paramITK["KT"] * data["UBTCulture"][j,:,:],
    )#[...,np.newaxis]


    # group 168
    # TigeUp := max(0, (TigeUp -  TigeUp * KNUp - TigeUp * KT * UBTCulture));
    data["TigeUp"][j:,:,:] = np.maximum(
        0,
        data["TigeUp"][j,:,:] - data["TigeUp"][j,:,:] * paramITK["KNUp"] - data["TigeUp"][j,:,:] * paramITK["KT"] * data["UBTCulture"][j,:,:],
    )#[...,np.newaxis]
    
    #// D�gradation des feuilles et tiges couch�es (liti�re)
    # group 169
    # LitFeuille :=  max(0, (LitFeuille -  LitFeuille * KNLit - LitFeuille * KI * UBTCulture  - LitFeuille * KT * UBTCulture));
    data["LitFeuille"][j:,:,:] = np.maximum(
        0,
        data["LitFeuille"][j,:,:] - data["LitFeuille"][j,:,:] * paramITK["KNLit"] - data["LitFeuille"][j,:,:] * paramITK["KI"] \
            * data["UBTCulture"][j,:,:] - data["LitFeuille"][j,:,:] * paramITK["KT"] * data["UBTCulture"][j,:,:],
    )#[...,np.newaxis]

    # group 170
    # LitTige :=  max(0, (LitTige -  LitTige * KNLit - LitTige * KT * UBTCulture));
    data["LitTige"][j:,:,:] = np.maximum(
        0,
        data["LitTige"][j,:,:] - data["LitTige"][j,:,:] * paramITK["KNLit"] - data["LitTige"][j,:,:] * paramITK["KT"] * data["UBTCulture"][j,:,:],
    )#[...,np.newaxis]

    # group 171
    #BiomMc := LitFeuille + LitTige;
    data["biomMc"][j:,:,:] = (data["LitFeuille"][j,:,:] + data["LitTige"][j,:,:])#[...,np.newaxis]
     
    # #// transfert dress� � liti�re effet pi�tinement
    # LitFeuille :=  LitFeuille + FeuilleUp * KT * UBTCulture;
    # group 172
    data["LitFeuille"][j:,:,:] = (data["LitFeuille"][j,:,:] + data["FeuilleUp"][j,:,:] * paramITK["KT"] * data["UBTCulture"][j,:,:])#[...,np.newaxis]

    # LitTige :=  LitTige + TigeUp * KT * UBTCulture;
    # group 173
    data["LitTige"][j:,:,:] = (data["LitTige"][j,:,:] + data["TigeUp"][j,:,:] * paramITK["KT"] * data["UBTCulture"][j,:,:])#[...,np.newaxis]

    # // le 01/03 on consid�re que toutes les pailles et feuilles dressees sont couchees

    #       if (trunc(DayOfTheYear(DateEnCours)) = 61) then
    #   begin
    #     LitFeuille :=  LitFeuille + FeuilleUp;
    #     LitTige :=  LitTige + TigeUp;
    #     FeuilleUp :=  0;
    #     TigeUp :=  0;
    #     BiomMc := LitFeuille + LitTige;
    #  end;

    return data




def MAJBiomMcSV3(data):
    """
    groupe 182
 A la Recolte, on calcul la part des biomasses qui restent sur place (Up), non r�colt�es
 et la part qui est mise � terre (Liti�re) sur ce qui est laiss� sur place
 On met a jour aussi la biomasse des liti�res pour les calculs effet mulch sue lr bilan hydrique
    """
#         if (NumPhase =7) then
#     begin
        # groupe 175
#       FeuilleUp := FeuilleUp +  BiomasseFeuilles * (1-TxRecolte);
        # groupe 176
#       TigeUp := TigeUp + BiomasseTiges *  (1-TxRecolte);

        # groupe 177
#       LitFeuille := LitFeuille + FeuilleUp * TxaTerre;

        # groupe 178
#       LitTige := LitTige + TigeUp * TxaTerre;

        # groupe 179
#       FeuilleUp := FeuilleUp * (1-TxaTerre);

        # groupe 180
#       TigeUp := TigeUp * (1-TxaTerre);
# //      LitTige := LitTige + BiomMc;
        # groupe 181
#       BiomMC := LitFeuille + LitTige;
#  {     BiomasseFeuilles := 0;
#       BiomasseTiges := 0;
    return data


def estimate_critical_nitrogen_concentration(j, data):
    """Estimate critical nitrogen concentration from total biomass.

    ``Ncrit = 5.35 * (biomasseTotale / 1000) ** (-0.44)``

    `biomasseTotale / 1000` converts kg/ha to t/ha. This is related to
    critical nitrogen dilution curves, but the biomass basis and coefficients
    still need crop-model validation.

    Source status: source-related to Justes-type dilution curves, not validated
    as an exact Justes implementation.
    """
    # estimate critical nitrogen concentration from plant dry matter using the Justes et al (1994) relationship
    data["Ncrit"][j,:,:] = 5.35 * (data["biomasseTotale"][j,:,:]/1000) ** (-0.44)
    return data
