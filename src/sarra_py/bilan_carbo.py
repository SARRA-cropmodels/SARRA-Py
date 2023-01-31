import numpy as np

def InitiationCulture(data, grid_width, grid_height, duration, paramVariete):
    """
    Initializes variables related to crop growth in the data xarray dataset.
    This code has been adapted from the original InitiationCulture procedure, MilBilanCarbone.pas code.
    Comments with tab indentation are from the original code.
    As the rain is the first variable to be initialized in the data xarray dataset, its dimensions are used
    to initialize the other variables.
    """    

    # Maximum thermal time (°C.j)
    # Somme de degré-jour maximale (°C.j)
    #   SommeDegresJourMaximale := SeuilTempLevee + SeuilTempBVP + SeuilTempRPR + SeuilTempMatu1 + SeuilTempMatu2;
    data["sommeDegresJourMaximale"] = (data["rain"].dims, np.full(
        (duration, grid_width, grid_height),
        (paramVariete["SDJLevee"] + paramVariete["SDJBVP"] + paramVariete["SDJRPR"] + paramVariete["SDJMatu1"] + paramVariete["SDJMatu2"])
    ))
    data["sommeDegresJourMaximale"].attrs = {"units":"°C.j", "long_name":"Maximum thermal time"}

    
    # Other variables to be initialized at 0
    # Autres variables à initialiser à 0
    #   NumPhase := 0;
    #   SommeDegresJour := 0;
    #   BiomasseAerienne := 0;
    #   BiomasseVegetative := 0;
    #   BiomasseTotale := 0;
    #   BiomasseTiges := 0;
    #   BiomasseRacinaire := 0;
    #   BiomasseFeuilles := 0;
    #   DeltaBiomasseTotale := 0;
    #   SeuilTempPhaseSuivante:=0;
    #   Lai := 0;
    variables = {
        "numPhase":"arbitrary units",
        "sdj":"°C.j",
        "biomasseAerienne":"kg/ha",
        "biomasseVegetative":"kg/ha",
        "biomasseTotale":"kg/ha",
        "biomasseTige":"kg/ha",
        "biomasseRacinaire":"kg/ha",
        "biomasseFeuille":"kg/ha",
        "deltaBiomasseTotale":"kg/ha",
        "seuilTempPhaseSuivante":"°C.j",
        "lai":"m2/m2",
    }
        
    for variable in variables :
        data[variable] = (data["rain"].dims, np.zeros(shape=(duration, grid_width, grid_height)))
        data[variable].attrs = {"units":variables[variable], "long_name":variable}

    return data





def InitSup(data, grid_width, grid_height, duration, paramTypeSol, paramITK):
    """
    Initializes supplementary variables needed for computations.
    As the rain is the first variable to be initialized in the data xarray dataset, its dimensions are used
    to initialize the other variables.
    """   

    data = data.copy(deep=True)

    variables = {
        "assim": ["",""],
        "assimPot": ["",""],
        "biomTotStadeFloraison": ["",""],
        "biomTotStadeIp": ["",""],
        "bM": ["",""],
        "changePhase" : ["indicator of phase transition","binary"],
        "cM": ["",""],
        "consoRur": ["",""],
        "conv": ["",""],
        "correctedIrrigation" : ["corrected irrigation","mm"],
        "cstr" : ["drought stress coefficient", "arbitrary unit"],
        "dayBiomLeaf": ["",""],
        "dayVrac" : ["modulated daily root growth","mm/day"],
        "ddj": ["daily thermal time","°C"],
        "deltaBiomasseAerienne": ["",""],
        "deltaBiomasseFeuilles": ["",""],
        #! renaming deltaRur with delta_root_tank_capacity
        #// "deltaRur": ["change in root system water reserve","mm"],
        "delta_root_tank_capacity": ["change in root system water reserve","mm"],
        "dr": ["",""],
        "dRdtPot": ["",""],
        "dureeDuJour": ["",""],
        #! replacing eauCaptee by water_gathered_by_mulch
        #// "eauCaptee" : ["water captured by the mulch in one day","mm"],
        "water_gathered_by_mulch" : ["water captured by the mulch in one day","mm"],
        "eauDispo" : ["available water, sum of rainfall and total irrigation for the day","mm"],
        "eauTranspi": ["",""],
        "etm": ["",""],
        "etp": ["",""],
        "etr": ["",""],
        "evap": ["",""],
        "evapPot": ["",""],
        "FEMcW": ["",""],
        "fesw": ["",""],
        "FeuilleUp": ["",""],
        "ftsw": ["",""],
        "initPhase": ["",""],
        "irrigTotDay" : ["total irrigation for the day","mm"],
        "KAssim": ["",""],
        "kce": ["",""],
        "kcp": ["",""],
        "kcTot": ["",""],
        "kRespMaint": ["",""],
        "LitFeuille": ["",""],
        "lr" : ["daily water runoff","mm"],
        "manqueAssim": ["",""],
        "nbJourCompte": ["",""],
        "nbjStress": ["",""],
        "NbUBT": ["",""],
        "pFact": ["",""],
        "phaseDevVeg": ["",""],
        "phasePhotoper": ["photoperiodic phase indicator","binary"],
        "rapDensite": ["",""],
        "rdt": ["",""],
        "rdtPot": ["",""],
        "reallocation": ["",""],
        "respMaint": ["",""],

        #! renaming ruIrr to irrigation_tank_capacity
        #//"ruIrr" : ["?","mm"],
        "irrigation_tank_capacity" : ["irrigation tank capacity","mm"],
        "ruRac": ["Water column that can potentially be strored in soil volume explored by root system","mm"],
        "seuilTempPhasePrec": ["",""],
        "sla": ["",""],
        "sommeDegresJourPhasePrec": ["",""],
        "startLock": ["",""],
        #! renaming stockIrr to irrigation_tank_stock
        #// "stockIrr" : ["?","mm"],
        "irrigation_tank_stock" : ["?","mm"],
        #! renaming stockMc to mulch_water_stock
        #// "stockMc" : ["water stored in crop residues (mulch)","mm"],
        "mulch_water_stock" : ["water stored in crop residues (mulch)","mm"],
        "stockRac": ["",""],
        # renaming stRu to root_tank_stock
        #// "stRu": ["",""],
        "root_tank_stock": ["",""],

        #! renaming stRuMax to total_tank_capacity
        #//"stRuMax": ["",""],
        "total_tank_capacity": ["",""],
        # renaming stRur to 
        "stRur": ["",""],
        #! renaming stRurMaxPrec to root_tank_capacity_previous_season
        # "stRurMaxPrec": ["",""],
        "root_tank_capacity_previous_season": ["",""],
        "stRurPrec": ["",""],
        "stRurSurf": ["",""],
        #! renaming stRuSurf to surface_tank_stock
        #// "stRuSurf": ["",""],
        "surface_tank_stock": ["",""],
        "stRuSurfPrec": ["",""],

        #! renaming stRuVar to delta_total_tank_stock
        #// "stRuVar": ["",""],
        "delta_total_tank_stock": ["",""],
        "sumPP": ["",""],
        "TigeUp": ["",""],
        "tr": ["",""],
        "trPot": ["",""],
        "trSurf": ["",""],
        "UBTCulture": ["",""],
        "vRac" : ["reference daily root growth","mm/day"],
    }
    


    for variable in variables :
        data[variable] = (data["rain"].dims, np.zeros(shape=(duration, grid_width, grid_height)))
        data[variable].attrs = {"units":variables[variable][1], "long_name":variables[variable][0]}


    data["irrigAuto"] = (data["rain"].dims, np.full((duration, grid_width, grid_height), paramITK["irrigAuto"]))
    data["irrigAuto"].attrs = {"units":"binary", "long_name":"automatic irrigation indicator"}


    return data


def InitSup2(data, grid_width, grid_height, duration, df_weather):
    data["tpMoy"] = df_weather["TEMP"].copy().values.reshape(grid_width, grid_height, duration)
    data["rain"] = df_weather["RAIN"].copy().values.reshape(grid_width, grid_height, duration)
    data["ET0"] = df_weather["ET0"].copy().values.reshape(grid_width, grid_height, duration)
    data["rg"] = df_weather["IRRAD"].copy().values.reshape(grid_width, grid_height, duration)
    return data


def EvalPar(data):
    #depuis meteo.par
    kpar = 0.5
    data["par"] = kpar * data["rg"]
    data["par"].attrs = {"units":"MJ/m2", "long_name":"par"}
    return data

    

def estimate_kcp(j, data, paramVariete):
    """
    This function estimates the kcp coefficient.
    
    It performs computation of kcp based on the maximum crop coefficient kcMax,
    as well as plant cover ltr.

    This function is based on the EvolKcpKcIni procedure, from the biomasse.pas,
    exmodules 1 & 2.pas files of the original PASCAL code.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramVariete (_type_): _description_

    Returns:
        _type_: _description_
    """
    # group 50

    data["kcp"][j:,:,:] = np.where(
        data["numPhase"][j,:,:] >= 1,
        np.maximum(0.3, paramVariete["kcMax"] * (1 - data["ltr"][j,:,:])),
        data["kcp"][j,:,:],
    )
    
    return data




def EvalLtr(j, data, paramVariete):
    # group 80
    # d'après biomasse.pas 

    
    # ltr : Taux de rayonnement transmis au sol. Unités : MJ/MJ
    data["ltr"][j:,:,:] = np.exp(-paramVariete["kdf"] * data["lai"][j,:,:])#[...,np.newaxis]
    
    return data




def EvalConversion(j, data, paramVariete):
    # d'après milbilancarbone.pas 
    # group 87

    # EvalConversion
    # group 81
    data["KAssim"][j:,:,:] = np.where(
        data["numPhase"][j,:,:] == 2,
        1,
        data["KAssim"][j,:,:],
    )#[...,np.newaxis]

    # group 82
    data["KAssim"][j:,:,:] = np.where(
        data["numPhase"][j,:,:] == 3,
        paramVariete['txAssimBVP'],
        data["KAssim"][j,:,:],
    )#[...,np.newaxis]

    # group 83
    data["KAssim"][j:,:,:] = np.where(
        data["numPhase"][j,:,:] == 4,
        paramVariete['txAssimBVP'],
        data["KAssim"][j,:,:],
    )#[...,np.newaxis]

    # group 84
    data["KAssim"][j:,:,:] = np.where(
        data["numPhase"][j,:,:] == 5,
        paramVariete["txAssimBVP"] + (data['sdj'][j,:,:] - data['sommeDegresJourPhasePrec'][j,:,:]) * (paramVariete['txAssimMatu1'] -  paramVariete['txAssimBVP']) / (data['seuilTempPhaseSuivante'][j,:,:] - data['sommeDegresJourPhasePrec'][j,:,:]),
        data["KAssim"][j,:,:],
    )#[...,np.newaxis]

    # group 85
    data["KAssim"][j:,:,:] = np.where(
        data["numPhase"][j,:,:] == 6,
        paramVariete["txAssimMatu1"] + (data["sdj"][j,:,:] - data["sommeDegresJourPhasePrec"][j,:,:]) * (paramVariete["txAssimMatu2"] - paramVariete["txAssimMatu1"]) / (data["seuilTempPhaseSuivante"][j,:,:] - data["sommeDegresJourPhasePrec"][j,:,:]),
        data["KAssim"][j,:,:],
    )#[...,np.newaxis]

    # group 86
    data["conv"][j:,:,:] = (data["KAssim"][j,:,:] * paramVariete["txConversion"])#[...,np.newaxis] # Conversion:=KAssim*EpsiB;

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




def BiomDensOptSarV42(j, data, paramITK, paramVariete):
    """
    d'après bilancarbonsarra.pas

    { si densit� plus faible alors on consid�re qu'il faut augmenter les biomasses, LAI etc
    en regard de cette situation au niveau de chaque plante (car tout est rapport� � des kg/ha).
    Si elle est plus forte elle augmente de fa�on asymptotique.
    }

    """

    if ~np.isnan(paramVariete["densOpti"]) :

        # group 88
        data["rapDensite"] = paramVariete["densiteA"] + paramVariete["densiteP"] * np.exp(-(paramITK["densite"] / ( paramVariete["densOpti"]/- np.log((1 - paramVariete['densiteA'])/ paramVariete["densiteP"]))))
        
        # group 89
        data["rdt"][j:,:,:] = (data["rdt"][j,:,:] * data["rapDensite"])#[...,np.newaxis]

        # group 90
        data["rdtPot"][j:,:,:] = (data["rdtPot"][j,:,:] * data["rapDensite"])#[...,np.newaxis]

        # group 91
        data["biomasseRacinaire"][j:,:,:] = (data["biomasseRacinaire"][j,:,:] * data["rapDensite"])#[...,np.newaxis]
        # group 92
        data["biomasseTige"][j:,:,:] = (data["biomasseTige"][j,:,:] * data["rapDensite"])#[...,np.newaxis]
        # group 93
        data["biomasseFeuille"][j:,:,:] = (data["biomasseFeuille"][j,:,:] * data["rapDensite"])#[...,np.newaxis]

        # group 94
        data["biomasseAerienne"][j:,:,:] = (data["biomasseTige"][j,:,:] + data["biomasseFeuille"][j,:,:] + data["rdt"][j,:,:])#[...,np.newaxis]
        #data["biomasseAerienne"][j:,:,:] = data["biomasseAerienne"][j,:,:] * data["rapDensite"]
        
        # group 95
        data["lai"][j:,:,:]  = (data["biomasseFeuille"][j,:,:] * data["sla"][j,:,:])#[...,np.newaxis]
        #data["lai"][j:,:,:]  = data["lai"][j:,:,:]  * data["rapDensite"]

        # group 96
        data["biomasseTotale"][j:,:,:] = (data["biomasseAerienne"][j,:,:] + data["biomasseRacinaire"][j,:,:])#[...,np.newaxis]
        #data["biomasseTotale"][j:,:,:] = data["biomasseTotale"][j:,:,:] * data["rapDensite"]
    
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
    





def EvalAssimSarrahV42(j, data, paramITK, paramVariete):

    """
    group 100
    d'après bilancarbonsarra.pas 

    Modif du 04/03/2021 : Prise en compte en plus de la densit� de semis de l'effet niveau d'intensification NI
    NI = 1 quand on est � l'optimum du niveau d'intensification. Dans le cas de situation contr�l� c'est
    la fertilit� qui est la clef principale en prenant en r�f�rence la qt� d'azote (�quivalent phosphore...) optimum
    Il peut aller � 0 ou �tre sup�rieur � 1 si situation sur optimum, ie un peu plus de rdt mais � cout trop �lev�...
    On �value un nouveau tx de conversion en fn du Ni au travers d'une double �quation : asympote x gaussienne invers�e
    Et d'un NI d�fini en fn du sc�nario de simulation ou des donn�es observ�es.
    NIYo = D�calage en Y de l'asymptote
    NIp  = pente de l'asymptote
    LGauss = Largeur de la Guaussienne
    AGauss = Amplitude de la Guaussienne

    Conversion qui est la valeur du taux de conversion en situation optimum n'a plus besoin d'�tre utilis� sinon
    dans la calibration des param�tres de cette �quation en absence de donn�es sur ces param�tres on ne met aucune valeur � NI
    CF fichier ex IndIntensite_txConv_eq.xls}

    """
    # on rajoute le parIntercepte depuis evalassimsarrahv4
    # data["parIntercepte"][j,:,:] = 0.5 * (1 - data["ltr"][j,:,:]) * data["rg"][j,:,:]

    # group 97
    if ~np.isnan(paramITK["NI"]): 
        #correction des taux de conversion en fonction des niveaux d'intensification
        # paramVariete["txConversion"] = paramVariete["NIYo"] + paramVariete["NIp"] * (1-np.exp(-paramVariete["NIp"] * paramITK["NI"])) - (np.exp(-0.5*((paramITK["NI"] - paramVariete["LGauss"])/paramVariete["AGauss"])* (paramITK["NI"]- paramVariete["LGauss"])/paramVariete["AGauss"]))/(paramVariete["AGauss"]*2.506628274631)

        data["assimPot"][j,:,:] = data["par"][j,:,:] * (1-np.exp(-paramVariete["kdf"] * data["lai"][j,:,:])) * paramVariete["txConversion"] * 10

    else :

        data["assimPot"][j,:,:] = data["par"][j,:,:] * (1-np.exp(-paramVariete["kdf"] * data["lai"][j,:,:])) * data["conv"][j,:,:] * 10

    # group 98
    data["assim"][j,:,:] = np.where(
        data["trPot"][j,:,:] > 0,
        data["assimPot"][j,:,:] * data["tr"][j,:,:] / data["trPot"][j,:,:],
        0,
    )


    return data




def EvalRespMaintSarrahV3(j, data, paramVariete):
    """
    # group 103
    d'après bilancarbonsarra.pas
    
    RespMaint Kg/ha/j  en équivalent matiére séche
    KRespMaint     (0.015)
    KTempMaint éC  (25 )
    """

    # group 101
    # on cast sur j
    # kRespMaint = txRespMaint ?
    # dRespMaint = respMaint ?
    data["respMaint"][j,:,:] =  ((paramVariete["kRespMaint"] * data["biomasseTotale"][j,:,:] * (2**((data["tpMoy"][j,:,:] - paramVariete["tempMaint"]) / 10)))) + (paramVariete["kRespMaint"] * data["biomasseFeuille"][j,:,:] * (2**((data["tpMoy"][j,:,:] -  paramVariete["tempMaint"]) / 10)))

    # group 102
    # Question pourquoi > 4 tous le s !!! si pas de feuilles mort !!! 
    # # on cast sur j	
    data["respMaint"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] > 4) & (data["biomasseFeuille"][j,:,:]==0),
        0,
        data["respMaint"][j,:,:],
    )#[...,np.newaxis]

    return data




def EvolBiomTotSarrahV4(j, data, paramVariete, paramITK):
    """
    groupo 106
    d'après bilancarbonsarra.pas
    {
    On harmonise avec une biomasse rapportée é une plante
    et pas par hectare pour l'initialisation de la biomasse é l'émergenceé phase 2
    }
    """

    ##! attention au pb de densité de semis à corriger

        #biomasse totale en kg/ha
    # on initialise en date du passage à la phase 2,
    # sino, biomasse totale fonction de la biomasse totale t-1 

    # BiomasseTotale := Densite* Max(1,70000/Densite) * KResGrain * BiomasseGrain / 1000;
    
    # group 104
    data["biomasseTotale"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:]==2) & (data["changePhase"][j,:,:]==1),
        paramITK["densite"] *  np.maximum(1,paramVariete['densOpti']/paramITK['densite']) * paramVariete["txResGrain"] *  paramVariete["poidsSecGrain"] / 1000,
        # paramITK["densite"] *  np.maximum(1,70000/paramITK['densite']) * paramVariete["txResGrain"] *  paramVariete["poidsSecGrain"] / 1000,
        data["biomasseTotale"][j,:,:]  + (data["assim"][j,:,:] - data["respMaint"][j,:,:]),
    )#[...,np.newaxis]

    

    # on cast sur j
    data["deltaBiomasseTotale"][j:,:,:] = (data["assim"][j,:,:] - data["respMaint"][j,:,:]).copy()#[...,np.newaxis]

    return data





def EvalRdtPotRespSarrahV4(j, data, paramVariete):

    """
    data["biomTotStadeIp"][j,:,:] = np.where(
        (data["numPhase"][j,:,:] == 4) & (data["changePhase"][j,:,:] == 1),
        data["biomasseTotale"][j,:,:],
        data["biomTotStadeIp"][j,:,:],
    )

    data["biomTotStadeFloraison"][j,:,:] = np.where(
        (data["numPhase"][j,:,:] == 4) & (data["changePhase"][j,:,:] == 1),
        data["biomasseTotale"][j,:,:],
        data["biomTotStadeFloraison"][j,:,:],
    )

    data["rdtPot"][j,:,:] = np.where(
        (data["numPhase"][j,:,:] == 4) & (data["changePhase"][j,:,:] == 1),
        (paramVariete["KRdtPotA"] * (data["biomTotStadeFloraison"][j,:,:] - data["biomTotStadeIp"][j,:,:]) + paramVariete["KRdtPotB"]) + paramVariete["KRdtBiom"] * data["biomTotStadeFloraison"][j,:,:],
        data["rdtPot"][j,:,:],
    )

    
    data["rdtPot"][j,:,:] = np.where(
        (data["rdtPot"][j,:,:] > data["biomasseTotale"][j,:,:]) & (data["numPhase"][j,:,:] < 6),
        data["biomasseTotale"][j,:,:],
        data["rdtPot"][j,:,:],
    )

    data["dRdtPot"][j,:,:] = np.where(
        (data["numPhase"][j,:,:] == 5) & (data["trPot"][j,:,:]>0),
        np.maximum(
            data["rdtPot"][j,:,:] * (data["ddj"][j,:,:] / paramVariete["SDJMatu1"]) * (data["tr"][j,:,:] / data["trPot"][j,:,:]),
            data["respMaint"][j,:,:] * 0.15,
        ),
        0,
    )
    """
    return data




def EvalRdtPotRespSarV42(j, data, paramVariete):
    # group 111
    # d'après bilancarbonsarra.pas

    #! biomTotStadeIp laissé à 0 ?
    # data["biomTotStadeIp"][j:,:,:] = np.where(
    #     (data["numPhase"][j,:,:] == 4) & (data["changePhase"][j,:,:] == 1),
    #     data["biomasseTotale"][j,:,:],
    #     data["biomTotStadeIp"][j,:,:],
    # )

    # group 107
    data["biomTotStadeFloraison"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 5) & (data["changePhase"][j,:,:] == 1),
        data["biomasseTotale"][j,:,:],
        data["biomTotStadeFloraison"][j,:,:],
    )#[...,np.newaxis]


    #group 108
    data["rdtPot"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 5) & (data["changePhase"][j,:,:] == 1),
        (paramVariete["KRdtPotA"] * (data["biomTotStadeFloraison"][j,:,:] - data["biomTotStadeIp"][j,:,:]) + paramVariete["KRdtPotB"]) + paramVariete["KRdtBiom"] * data["biomTotStadeFloraison"][j,:,:],
        data["rdtPot"][j,:,:],
    )#[...,np.newaxis]

    #group 109
    #! phaseDevVeg pas utilisé ? attention c'est un paramètre variétal et pas un jeu de donées
    data["rdtPot"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 5) & (data["changePhase"][j,:,:] == 1) & (data["rdtPot"][j,:,:] > data["biomasseTige"][j,:,:] * 2) & (data["phaseDevVeg"][j,:,:] < 6),
        data["biomasseTige"][j,:,:] * 2,
        data["rdtPot"][j,:,:],
    )#[...,np.newaxis]

    # group 110
    # dRdtPot = rdtPotDuJour
    data["dRdtPot"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 5),
        np.where(
            (data["trPot"][j,:,:]>0),
            np.maximum(
                #! pourquoi est ce que c'est un rapport de ddj sur sdj, et pas sdj sur sdj ?
                data["rdtPot"][j,:,:] * (data["ddj"][j,:,:] / paramVariete["SDJMatu1"]) * (data["tr"][j,:,:] / data["trPot"][j,:,:]),
                data["respMaint"][j,:,:] * 0.15,
            ),
            0,
        ),
        data["dRdtPot"][j,:,:],
    )#[...,np.newaxis]

    
    return data





def EvolBiomAeroSarrahV3(j, data, paramVariete):
    # group 115
    #  verif vs code pascal OK
    # d'après bilancarbonesarra.pas

    # on stocke la valeur précédente dans deltaBiomasseAerienne
    # deltabiomasseaerienne est juste la différence entre j et j-1
    # group 112
    data["deltaBiomasseAerienne"][j:,:,:] = np.copy(data["biomasseAerienne"][j,:,:])#[...,np.newaxis]

    # la biomasseAerienne est égale, sur les stades 2 à 4, à un coeff borné au max en 0.9
    # fois la biomasse totale
    # en dehors de ces stades, elle vaut la différence entre la biomasse totale
    # et la biomasse aerienne
    # on étend sur j
    #group 113
    data["biomasseAerienne"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] >= 2) & (data["numPhase"][j,:,:] <= 4),
        np.minimum(0.9, paramVariete["aeroTotPente"] * data["biomasseTotale"][j,:,:] + paramVariete["aeroTotBase"]) * data["biomasseTotale"][j,:,:],
        data["biomasseAerienne"][j,:,:] + data["deltaBiomasseTotale"][j,:,:],
    )#[...,np.newaxis]




    # version ocelet
    # data["deltaBiomasseAerienne"][j:,:,:] = (data["biomasseAerienne"][j,:,:] - data["deltaBiomasseArienne"][j,:,:])
    # version originale
    # group 114
    data["deltaBiomasseAerienne"][j:,:,:] = (data["biomasseAerienne"][j,:,:] - data["deltaBiomasseAerienne"][j,:,:])#[...,np.newaxis]
    # version modifiée
    # data["deltaBiomasseAerienne"][j,:,:] = data["biomasseAerienne"][j,:,:] - data["biomasseAerienne"][j-1,:,:]


    
    
    return data




def EvalReallocationSarrahV3(j, data, paramVariete):
    """
    groupe 118
    d'après bilancarbonesarra.pas
    {
    La reallocation est é 0 quand la biomasse foliaire verte est inférieure é 30 kh/ha
    }
    """

    condition = (data["numPhase"][j,:,:] == 5)
        # on cast sur j
        # group 116
    data["manqueAssim"][j:,:,:] = np.where(
        condition,
        np.maximum(0, (data["dRdtPot"][j,:,:] -  np.maximum(0.0, data["deltaBiomasseAerienne"][j,:,:]))),
        0,
    )#[...,np.newaxis]
    # on cast sur j

    # group 117
    data["reallocation"][j:,:,:] = np.where(
        condition,
        np.minimum(data["manqueAssim"][j,:,:] *  paramVariete["txRealloc"],  np.maximum(0.0, data["biomasseFeuille"][j,:,:] - 30)),
        0,
    )#[...,np.newaxis]

    return data





def EvalBiomasseRacinaire(j, data):
    #d'après milbilancarbone.pas
    # groupe 119
    data["biomasseRacinaire"][j,:,:] = data["biomasseTotale"][j,:,:] - data["biomasseAerienne"][j,:,:]

    return data




def EvalFeuilleTigeSarrahV4(j, data, paramVariete):

    # d'après bilancarbonsarra.pas

    # on reset bM et CM en début de procédure

    # si numPhase > 1
    # group 120
    data["deltaBiomasseFeuilles"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] > 1),
        data["biomasseFeuille"][j,:,:],
        data["deltaBiomasseFeuilles"][j,:,:],
    )#[...,np.newaxis]


    #     {
    # Modif du 15/06/2020     Je ne sais pourquoi max(10 avant max(O � v�rifier si division par BiomasseFeuilles?
    # }
    # si deltaBiomasseAerienne < 0
    condition = (data["numPhase"][j,:,:] > 1) & \
        (data["deltaBiomasseAerienne"][j,:,:] < 0)

    # group 121
    data["biomasseFeuille"][j:,:,:] = np.where(
        condition,
        np.maximum(0.00000001, data["biomasseFeuille"][j,:,:] - (- data["deltaBiomasseAerienne"][j,:,:] + data["reallocation"][j,:,:]) \
             * paramVariete["pcReallocFeuille"]),
        data["biomasseFeuille"][j,:,:],
    )#[...,np.newaxis]

    # group 122
    data["biomasseTige"][j:,:,:] = np.where(
        condition,
        np.maximum(0.00000001, data["biomasseTige"][j,:,:] - (- data["deltaBiomasseAerienne"][j,:,:] + data["reallocation"][j,:,:]) \
            * (1 - paramVariete["pcReallocFeuille"])),
        data["biomasseTige"][j,:,:],
    )#[...,np.newaxis]



    # si deltaBiomasseAerienne >= 0
    condition = (data["numPhase"][j,:,:] > 1) & \
        (data["deltaBiomasseAerienne"][j,:,:] >= 0) & \
        ((data["numPhase"][j,:,:] <= 4) | (data["numPhase"][j,:,:] <= paramVariete["phaseDevVeg"]))
        # (data["numPhase"][j,:,:] <= 4)



    # group 123
    data["bM"][j,:,:] = np.where(
        condition,
        paramVariete["feuilAeroBase"] - 0.1,
        data["bM"][j,:,:],
    )


    # group 124
    data["cM"][j,:,:] = np.where(
        condition,
        ((paramVariete["feuilAeroPente"] * 1000)/ data["bM"][j,:,:] + 0.78) / 0.75,
        data["cM"][j,:,:],
    )


    # group 125
    data["biomasseFeuille"][j:,:,:] = np.where(
        condition,
        (0.1 + data["bM"][j,:,:] * data["cM"][j,:,:] ** ((data["biomasseAerienne"][j,:,:] - data["rdt"][j,:,:]) / 1000)) \
             * (data["biomasseAerienne"][j,:,:] - data["rdt"][j,:,:]),
        data["biomasseFeuille"][j,:,:],
    )#[...,np.newaxis]




    # group 126
    data["biomasseTige"][j:,:,:] = np.where(
        condition,
        data["biomasseAerienne"][j,:,:] - data["biomasseFeuille"][j,:,:] - data["rdt"][j,:,:],
        data["biomasseTige"][j,:,:],
    )#[...,np.newaxis]


    
    condition = (data["numPhase"][j,:,:] > 1) & \
        (data["deltaBiomasseAerienne"][j,:,:] >= 0)

    # group 127
    data["biomasseFeuille"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] > 1) & (data["deltaBiomasseAerienne"][j,:,:] > 0),
        data["biomasseFeuille"][j,:,:] - data["reallocation"][j,:,:] * paramVariete["pcReallocFeuille"],
        data["biomasseFeuille"][j,:,:],
    )#[...,np.newaxis]


    # group 128
    data["biomasseTige"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] > 1) & (data["deltaBiomasseAerienne"][j,:,:] > 0),
        data["biomasseTige"][j,:,:] - (data["reallocation"][j,:,:] * (1- paramVariete["pcReallocFeuille"])),
        data["biomasseTige"][j,:,:],
    )#[...,np.newaxis]



    condition = (data["numPhase"][j,:,:] > 1) 

    # group 129
    data["deltaBiomasseFeuilles"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] > 1),
        data["biomasseFeuille"][j,:,:] - data["deltaBiomasseFeuilles"][j,:,:],
        data["deltaBiomasseFeuilles"][j,:,:],
    )#[...,np.newaxis]

    #group 130
    data["biomasseAerienne"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] > 1),
        data["biomasseTige"][j,:,:] + data["biomasseFeuille"][j,:,:] + data["rdt"][j,:,:],
        data["biomasseAerienne"][j,:,:],
    )#[...,np.newaxis]



    return data




def EvalBiomasseVegetati(j, data):
    # group 132
    #d'après milbilancarbone.pas
    data["biomasseVegetative"][j:,:,:] = (data["biomasseTige"][j,:,:] + data["biomasseFeuille"][j,:,:])#[...,np.newaxis]
    return data




def EvalSlaSarrahV3(j, data, paramVariete):
    # check vs code pascal OK
    """
    groupe 136
    d'après bulancarbonsarra.pas

    On suppose que les jeunes feuilles on un SLA supérieur aux vieilles feuilles.
    La fraction de jeunes (nouvelles) feuilles fait donc monter le SLA global
    du couvert. Le paramétre penteSLA provoque une chute générale du SLA
    (penteSLA = chute relative par jour = fraction de différence entre SLAmax
    et SLAmin). Fonctionnement conéu surtout pour les légumineuses, mais
    peut étre aussi adapté aux autres espéces.
    Paramétres :
    SLAmax (0.001 é 0.01), ex : 0.007
    SLAmin (0.001 é 0.01), ex : 0.002
    penteSLA (0 é 0.2), ex : 0.1
    Avec : SLAini = SLAmax
    }
    """
    # group 133
    data["sla"][j:,:,:] = np.where(
        (data["biomasseFeuille"][j,:,:] > 0) & \
            (data["numPhase"][j,:,:] == 2) & \
            (data["changePhase"][j,:,:] == 1),
        paramVariete["slaMax"],
        data["sla"][j,:,:],
    )#[...,np.newaxis]

    # Modif du 10/07/2018, DeltaBiomasse neg si reallocation ne pas fair l'evol du SLA dans ces conditions
    
    # original
    # groupe 134
    data["sla"][j:,:,:] = np.where(
        (data["biomasseFeuille"][j,:,:] > 0),
        np.where(
            (data["deltaBiomasseFeuilles"][j,:,:] > 0),
            (data["sla"][j,:,:] - paramVariete["slaPente"] * (data["sla"][j,:,:] - paramVariete["slaMin"])) \
              * (data["biomasseFeuille"][j,:,:] - data["deltaBiomasseFeuilles"][j,:,:]) / data["biomasseFeuille"][j,:,:] \
              + (paramVariete["slaMax"] + data["sla"][j,:,:])/2 * (data["deltaBiomasseFeuilles"][j,:,:] / data["biomasseFeuille"][j,:,:]),
            (data["sla"][j,:,:] - paramVariete["slaPente"] * (data["sla"][j,:,:] - paramVariete["slaMin"])) \
                * (data["biomasseFeuille"][j,:,:] / data["biomasseFeuille"][j,:,:]),
        ),
        data["sla"][j,:,:],
    )#[...,np.newaxis]

    # d'après version ocelet
    # data["sla"][j:,:,:] = np.where(
    #     (data["biomasseFeuille"][j,:,:] > 0),
    #     (data["sla"][j,:,:] - paramVariete["slaPente"] * (data["sla"][j,:,:] - paramVariete["slaMin"])) \
    #         * (data["biomasseFeuille"][j,:,:] - data["deltaBiomasseFeuilles"][j,:,:]) / data["biomasseFeuille"][j,:,:] \
    #         + (paramVariete["slaMax"] + data["sla"][j,:,:])/2 * (data["deltaBiomasseFeuilles"][j,:,:] / data["biomasseFeuille"][j,:,:]),
    #     data["sla"][j,:,:],
    # )

    # mix original/ocelet
    # data["sla"][j:,:,:] = np.where(
    #     (data["biomasseFeuille"][j,:,:] > 0),
    #     np.where(
    #         (data["deltaBiomasseFeuilles"][j,:,:] > 0),
    #         (data["sla"][j,:,:] - paramVariete["slaPente"] * (data["sla"][j,:,:] - paramVariete["slaMin"])) * (data["biomasseFeuille"][j,:,:] - data["deltaBiomasseFeuilles"][j,:,:]) / data["biomasseFeuille"][j,:,:] + (paramVariete["slaMax"] + data["sla"][j,:,:])/2 * (data["deltaBiomasseFeuilles"][j,:,:] / data["biomasseFeuille"][j,:,:]),
    #         (data["sla"][j,:,:] - paramVariete["slaPente"] * (data["sla"][j,:,:] - paramVariete["slaMin"])) * (data["biomasseFeuille"][j,:,:] / data["deltaBiomasseFeuilles"][j,:,:]),
    #     ),
    #     data["sla"][j,:,:],
    # )

    # original modifié
    # data["sla"][j:,:,:] = np.where(
    #     (data["biomasseFeuille"][j,:,:] > 0),
    #     np.where(
    #         (data["deltaBiomasseFeuilles"][j,:,:] > 0),
    #         (data["sla"][j,:,:] - paramVariete["slaPente"] * (data["sla"][j,:,:] - paramVariete["slaMin"])) * (data["biomasseFeuille"][j,:,:] - data["deltaBiomasseFeuilles"][j,:,:]) / data["biomasseFeuille"][j,:,:] + (paramVariete["slaMax"] + data["sla"][j,:,:])/2 * (data["deltaBiomasseFeuilles"][j,:,:] / data["biomasseFeuille"][j,:,:]),
    #         (data["sla"][j,:,:] - paramVariete["slaPente"] * (data["sla"][j,:,:] - paramVariete["slaMin"])) * (data["biomasseFeuille"][j,:,:] / data["biomasseFeuille"][j,:,:]),
    #         # data["sla"][j,:,:],
    #     ),
    #     data["sla"][j,:,:],
    # )


    # groupe 135
    data["sla"][j:,:,:] = np.where(
        (data["biomasseFeuille"][j,:,:] > 0),
        # np.minimum(paramVariete["slaMin"], np.maximum(paramVariete["slaMax"], data["sla"][j,:,:])),
        np.minimum(paramVariete["slaMax"], np.maximum(paramVariete["slaMin"], data["sla"][j,:,:])), # d'après version ocelet
        data["sla"][j,:,:],
    )#[...,np.newaxis]

    

    return data




def EvolLAIPhases(j, data):
    # d'après milbilancarbone.pas
    # group 137
    data["lai"][j:,:,:] = np.where(
        #(data["numPhase"][j,:,:] <= 1),
        (data["numPhase"][j,:,:] <= 1) | (data["startLock"][j,:,:] == 1),
        0,
        np.where(
            data["numPhase"][j,:,:] <= 6,
            data["biomasseFeuille"][j,:,:] * data["sla"][j,:,:],
            0,
        )
    )#[...,np.newaxis]


    return data




def EvolDayRdtSarraV3(j, data):
    # groupe 138
    # d'après bilancarbonsarra.pas
    # {
    # On tend vers le potentiel en fn du rapport des degresJours/sumDegresJours
    # pour la phase de remplissage
    # Frein sup fn du flux de s�ve estim� par le rapport Tr/TrPot
    # }

    # dRdtPot = RdtPotDuJour
    # on cast sur j
    data["rdt"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 5),
        data["rdt"][j,:,:] + np.minimum(data["dRdtPot"][j,:,:],  np.maximum(0.0, data["deltaBiomasseAerienne"][j,:,:]) + data['reallocation'][j,:,:]),
        data["rdt"][j,:,:],
    )#[...,np.newaxis]


    return data




def BiomDensiteSarraV4(j, data, paramITK):
    """
    if ~np.isnan(paramVariete["densOpti"]):
        data["rapDensite"][j,:,:] = np.minimum(1, paramITK["densite"]/paramVariete["densOpti"])
        data["rdt"][j,:,:] = data["rdt"][j,:,:] * data["rapDensite"][j,:,:]
        data["rdtPot"][j,:,:] = data["rdtPot"][j,:,:] * data["rapDensite"][j,:,:]
        data["biomasseRacinaire"][j,:,:] = data["biomasseRacinaire"][j,:,:] * data["rapDensite"][j,:,:]
        data["biomasseTige"][j,:,:] = data["biomasseTige"][j,:,:] * data["rapDensite"][j,:,:]
        data["biomasseFeuille"][j,:,:] = data["biomasseFeuille"][j,:,:] * data["rapDensite"][j,:,:]
        data["biomasseAerienne"][j,:,:] = data["biomasseFeuille"][j,:,:] + data["biomasseTige"][j,:,:] + data["rdt"][j,:,:]
        data["lai"][j,:,:] = data["biomasseFeuille"][j,:,:] * data["sla"][j,:,:]
        data["biomasseTotale"][j,:,:] = data["biomasseAerienne"][j,:,:] + data["biomasseRacinaire"][j,:,:]
    """
    return data




def BiomDensiteSarraV42(j, data, paramITK, paramVariete):
    # depuis bilancarbonsarra.pas
    #group 160
    
    if ~np.isnan(paramVariete["densOpti"]):

        #! confusion entre rapDensite dataset et parametre
        #group 151
        paramITK["rapDensite"] = paramVariete["densiteA"] + paramVariete["densiteP"] * np.exp(-(paramITK["densite"] / ( paramVariete["densOpti"]/- np.log((1 - paramVariete['densiteA'])/ paramVariete["densiteP"]))))

        # group 152
        data["rdt"][j:,:,:] = (data["rdt"][j,:,:] / data["rapDensite"])#[...,np.newaxis]


        # group 153
        data["rdtPot"][j:,:,:] = (data["rdtPot"][j,:,:]/ data["rapDensite"])#[...,np.newaxis]

        # group 154
        data["biomasseRacinaire"][j:,:,:] = (data["biomasseRacinaire"][j,:,:] / data["rapDensite"])#[...,np.newaxis]

        # group 155
        data["biomasseTige"][j:,:,:] = (data["biomasseTige"][j,:,:] / data["rapDensite"])#[...,np.newaxis]

        # group 156
        data["biomasseFeuille"][j:,:,:] = (data["biomasseFeuille"][j,:,:] / data["rapDensite"])#[...,np.newaxis]

        # group 157
        data["biomasseAerienne"][j:,:,:] = (data["biomasseTige"][j,:,:] + data["biomasseFeuille"][j,:,:] + data["rdt"][j,:,:])#[...,np.newaxis] 
        #data["biomasseAerienne"][j:,:,:] = data["biomasseAerienne"][j,:,:] / data["rapDensite"]


        #? conflit avec fonction evolLAIphase ?
        #  group 158
        #data["lai"][j:,:,:]  = data["biomasseFeuille"][j,:,:] * data["sla"][j,:,:]
        data["lai"][j:,:,:]  = data["lai"][j:,:,:]  / data["rapDensite"]

        # group 159
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