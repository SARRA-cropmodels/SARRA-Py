import numpy as np
import xarray as xr

def InitPlotMc(data, grid_width, grid_height, paramITK, paramTypeSol, duration):
    """
    Initializes variables related to crop residues boimass (mulch) in the data xarray dataset.
    This code has been adapted from the original InitPlotMc procedure, Bileau.pas code.
    Comments with tab indentation are from the original code.
    As the rain is the first variable to be initialized in the data xarray dataset, its dimensions are used
    to initialize the other variables.
    """

    # Initial biomass of crop residues (mulch) (kg/ha)
    # Biomasse initiale des résidus de culture (mulch) (kg/ha)
    #   BiomMc := BiomIniMc;
    data["biomMc"] = (data["rain"].dims, np.full((duration, grid_width, grid_height), paramITK["biomIniMc"]))
    data["biomMc"].attrs = {"units": "kg/ha", "long_name": "Initial biomass of crop residues (mulch)"}


    # Initial biomass of stem residues as litter (kg/ha)
    # Biomasse initiale des résidus de tiges sous forme de litière (kg/ha)
    #   LitTiges := BiomIniMc;
    data["LitTige"] = (data["rain"].dims, np.full((duration, grid_width, grid_height), paramITK["biomIniMc"]))
    data["LitTige"].attrs = {"units": "kg/ha", "long_name": "Initial biomass of stem residues as litter"}


    # ?
    #   StSurf := StockIniSurf;
    # data["stSurf"] = np.full((grid_width, grid_height, duration), paramTypeSol["stockIniSurf"])


    # ?
    #   Ltr := 1;
    data["ltr"] = (data["rain"].dims, np.full((duration, grid_width, grid_height), 1.0))


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
    data["profRu"] = data["epaisseurProf"] + data["epaisseurSurf"]
    data["profRu"].attrs = {"units": "mm", "long_name": "Soil maximal depth"}


    # Maximum water capacity to humectation front (mm)
    # Quantité d'eau maximum jusqu'au front d'humectation (mm)
    #   // modif 10/06/2015  resilience stock d'eau
    #   // Front d'humectation egal a RuSurf trop de stress initial
    #   //    Hum := max(StTot, StRurMax);
    #   Hum := max(RuSurf, StRurMax);
    #   // Hum mis a profRuSurf
    #   Hum := max(StTot, Hum);
    data["hum"] = (data["rain"].dims, np.full((duration, grid_width, grid_height),
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
    data["hum"].attrs = {"units": "mm", "long_name": "Maximum water capacity to humectation front"}


    # Previous value for Maximum water capacity to humectation front (mm)
    #  HumPrec := Hum;
    data["humPrec"] = data["hum"]
    
    
    # ?
    #   StRurPrec := 0;


    # Previous value for stTot
    #   StRurMaxPrec := 0;
    #   //modif 10/06/2015 resilience stock d'eau
    #! renaming stTot with total_tank_stock
    #// data["stRuPrec"] =  data["stTot"]
    data["stRuPrec"] =  data["total_tank_stock"]
    


    return data




def Meteo0DegToRad(): #pas indispensable
    return None

def Meteo1AVGTempHum(): # pas indispensable
    return None

def Meteo2Decli(): # pas indispensable
    return None

def Meteo3SunPosi():# pas indispensable
    return None

def Meteo4DayLength():# pas indispensable
    return None

def Meteo5SunDistance():# pas indispensable
    return None

def Meteo6RayExtra():# pas indispensable
    return None

def Meteo7RgMax():# pas indispensable
    return None

def Meteo8InsToRg():# pas indispensable
    return None

def Meteo9Par():# pas indispensable
    return None

def MeteoEToFAO():# pas indispensable
    return None



def update_irrigation_tank_stock(j, data):
    """
    stockIrr : "water stock in the irrigation tank" (mm) // irrigation_tank_stock
    
    If we are in automatic irrigation mode, and between phases 0 and 6, and if
    root_tank_capacity is less than surface_tank_capacity, meaning in the
    simulation that roots haven't reached yet the limit between the surface
    compartment and deep compartment, then we define irrigation_tank_stock as
    equal to surface_tank_stock, that is to say, we give to
    irrigation_tank_stock a minimum value that equals surface_tank_stock. Else,
    we do not modify irrigation_tank_stock value.
    
    N.B. : for phase 7, we keep the existing irrigation_tank_stock value

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    condition = (data["irrigAuto"][j, :, :] == True) & \
        (data["numPhase"][j, :, :] > 0) & \
        (data["numPhase"][j, :, :] < 6)

    # group 1
    #! renaming stockIrr with irrigation_tank_stock
    #//data["stockIrr"][j, :, :] = np.where(
    data["irrigation_tank_stock"][j, :, :] = np.where(
        condition,
        xr.where(
            #! renaming stRurMax to root_tank_capacity
            #! renaming ruSurf with surface_tank_capacity
            #// (data["stRurMax"] < data["ruSurf"]),
            (data["root_tank_capacity"] < data["surface_tank_capacity"])[j, :, :],
            #! renaming stRuSurf to surface_tank_stock
            #// data["stRuSurf"][j, :, :],
            data["surface_tank_stock"][j, :, :],
            #! renaming stRur to root_tank_stock
            #// data["stRur"][j, :, :],
            data["root_tank_stock"][j, :, :],
        ),
        data["irrigation_tank_stock"][j, :, :],
    )

    return data



def update_irrigation_tank_capacity(j, data):
    """
    ruIrr : "maximum water capacity of irrigation tank" (mm) // irrigation_tank_capacity
    
    If we are in automatic irrigation mode, and between phases 0 and 6, and if
    root_tank_capacity is less than surface_tank_capacity, meaning that roots
    haven't reached the limit between the surface compartment and deep
    compartment, then we define irrigation_tank_capacity as equal to
    surface_tank_capacity, that is to say, we give to irrigation_tank_capacity a
    minimum value that equals surface_tank_capacity. else, we do not modify
    irrigation_tank_capacity value

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    # group 2
    condition = \
        (data["irrigAuto"][j, :, :] == True) & \
        (data["numPhase"][j, :, :] > 0) & \
        (data["numPhase"][j, :, :] < 6)

    # renaming ruIrr with irrigation_tank_capacity
    #// data["ruIrr"][j, :, :] = np.where(
    data["irrigation_tank_capacity"][j, :, :] = np.where(
        condition,
        np.where(
            #! renaming stRurMax to root_tank_capacity
            #! renaming ruSurf with surface_tank_capacity
            #// (data["stRurMax"] < data["ruSurf"]),
            data["root_tank_capacity"][j,:,:] < data["surface_tank_capacity"],
            #// data["ruSurf"],
            data["surface_tank_capacity"],
            #// data["stRurMax"],
            data["root_tank_capacity"][j,:,:],
        ),
        data["irrigation_tank_capacity"][j, :, :],
    )

    return data

def update_irrigTotDay(j, data, paramITK):
    """
    irrigTotDay : "total irrigation of the day, both from the irrigation history
    and the estimated irrigation need" (mm) // irrigation_total_day
    
    if we are in automatic irrigation mode, and between phases 0 and 6, and if
    the filling of the irrigation tank is below the target filling value
    (irrigAutoTarget, decimal percentage), we first compute 90% of the difference
    between irrigation_tank_stock and irrigation_tank_capacity (that is to say,
    90% of the volume needed to fill the irrigation tank), bounded by a minimum
    of 0 and a maximum of maxIrrig. Else, the computed value is 0.

    Then, we calculate the total irrigation of the day by summing the
    estimated irrigation need with the irrigation history of the day.

    Returns:
        _type_: _description_
    """

    #! renaming stockIrr with irrigation_tank_stock
    #! renaming ruIrr with irrigation_tank_capacity
    condition = (data["irrigAuto"][j, :, :] == True) & \
        (data["numPhase"][j, :, :] > 0) & \
        (data["numPhase"][j, :, :] < 6) & \
        (data["irrigation_tank_stock"][j, :, :] / data["irrigation_tank_capacity"][j,:,:] \
            < paramITK["irrigAutoTarget"])
        
    # group 3
    data["irrigTotDay"][j, :, :] = xr.where(
        condition,
        np.minimum(
            np.maximum(
                0,
                # ! replacing correctedIrrigation by irrigation
                #! renaming stockIrr with irrigation_tank_stock
                #! renaming ruIrr with irrigation_tank_capacity
                # // ((data["ruIrr"][j, :, :] - data["stockIrr"][j, :, :]) * 0.9) - data["correctedIrrigation"][j, :, :]),
                ((data["irrigation_tank_capacity"][j, :, :] - data["irrigation_tank_stock"][j, :, :]) * 0.9) \
                    - data["irrigation"][j, :, :]
                ),
            paramITK["maxIrrig"]
        ),
        0,
    )
    
    # group 4
    data["irrigTotDay"][j, :, :] = (
        # ! replacing correctedIrrigation by irrigation
        # // data["correctedIrrigation"][j, :, :] + data["irrigTotDay"][j, :, :]).copy()
        data["irrigation"][j, :, :] + data["irrigTotDay"][j, :, :])

    return data



def EvalIrrigPhase(j, data, paramITK):
    """
    Translated from the procedure EvalIrrigPhase, of the original Pascal codes
    bileau.pas and exmodules2.pas.

    In irrigAuto mode, this function computes the size and filling of the
    irrigation tank, and the irrigation demand, according to the irrigation
    target (irrigAutoTarget), the maximum irrigation capacity (maxIrrig), and
    the size and filling of the root zone (stRurMax, stRur) and the surface
    reservoir (stRuSurf, ruSurf).

    It first calculates stockIrr, the water stock in the irrigation tank, and
    ruIrr, the maximum water capacity of irrigation tank. Both stockIrr and
    ruIrr are given minimum boundaries related to properties of the surface
    reservoir. Then, it calculates the irrigation demand, irrigTotDay.

    irrigation_tank_stock and irrigation_tank_capacity are only computed in
    order to avoid issues with very shallow rooting, where calculation of
    filling of root_tank_capacity by root_tank_stock can be inappropriate and
    lead to inadapted results for automatic irrigation

    Notes from CB, 2014 :
    Modification due à la prise en compte effet Mulch Soit on a une irrigation
    observée, soit on calcul la dose d'irrigation Elle est calculée en fonction
    d'un seuil d'humidité (IrrigAutoTarget) et de possibilité technique ou choix
    (MaxIrrig, Precision) Dans cette gestion d'irrigation la pluie du jour n'est
    pas prise en compte

    N.B.: here, precision is not taken into account anymore
    """

    # First, we store initial irrigation value of the day in the
    # correctedIrrigation array
    # ! it does not seem definition and use of correctedIrrigation is useful
    # ! instead we will just use the already defined irrigation array
    # // data["correctedIrrigation"][j, :, :] = data["irrigation"][j, :, :].copy(deep=True)
    
    data = update_irrigation_tank_stock(j, data)
    data = update_irrigation_tank_capacity(j, data)
    data = update_irrigTotDay(j, data, paramITK)

    return data





def PluieIrrig(j, data):
    """
    Translated from the procedure PluieIrrig, of the original Pascal codes
    bileau.pas and exmodules2.pas

    This function computes the total water available for the day, by summing the
    rain and the irrigation.

    Notes from CB, 2014 :
    Hypotheses : Le mulch ajoute une couche direct sous la pluie et irrig, ici
    irrigTotDay qui est l'irrigation observée ou calculée, d'où on regroupe les
    deux avant calcul de remplissage du mulch et ensuite calcul du ruissellement.

    group 5
    """

    data["eauDispo"][j,:,:] = data["rain"][j,:,:] + data["irrigTotDay"][j,:,:]

    return data


def estimate_water_captured_by_mulch(j, data, paramITK):
    """
    Determination of water gathered by the mulch (eauCaptee, mm):
    
    We determine the quantity of water gathered by mulch by multiplying the
    available water (eauDispo, from rain and irrigation, mm) with a
    exponential function of covering capacity of the considered mulch
    (surfMc, ha/t) and the mulch biomass (biomMc, kg/ha), representing the
    fraction of soil covered by mulch. The value of eauCaptee is bounded by
    the maximum capacity of the mulch to gather water (humSatMc, kg H2O/kg
    biomass), minus stock of water already present in it (stockMc, mm).

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramITK (_type_): _description_

    Returns:
        _type_: _description_
    """

    # group 7
    #! modyfing variable names to improve readability
    #! replacing eauCaptee by water_gathered_by_mulch
    #! replacing stockMc by mulch_water_stock
    #// data["eauCaptee"][j,:,:] = np.minimum(
    data["water_gathered_by_mulch"][j,:,:] = np.minimum(
        data["eauDispo"][j,:,:] * (1 - np.exp(-paramITK["surfMc"] / 1000 * data["biomMc"][j,:,:])),
        #// (paramITK["humSatMc"] * data["biomMc"][j,:,:] / 10000) - data["stockMc"][j,:,:],
        (paramITK["humSatMc"] * data["biomMc"][j,:,:] / 10000) - data["mulch_water_stock"][j,:,:],
    )

    return data


def update_available_water_after_mulch_filling(j, data):
    """
    Updating available water (eauDispo, mm) : 
    
    As some water is gathered by the mulch, the available water is updated by
    subtracting the gathered water (eauCaptee, mm) from the total available
    water (eauDispo, mm). This value is bounded by 0, as the available water
    cannot be negative.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """
    # ! correction as broadcasting on xarray seems less constrained than on numpy
    #! modyfing variable names to improve readability
    #! replacing eauCaptee by water_gathered_by_mulch
    # group 8
    #// data["eauDispo"][j:,:,:] =  np.maximum(data["eauDispo"][j,:,:] - data["eauCaptee"][j,:,:], 0) # //[...,np.newaxis]
    data["eauDispo"][j:,:,:] =  np.maximum(data["eauDispo"][j,:,:] - data["water_gathered_by_mulch"][j,:,:], 0) # //[...,np.newaxis]
    
    return data

def update_mulch_water_stock(j, data):
    """
    Updating water stock in mulch (stockMc, mm) :
    The water stock in mulch is updated by adding the gathered water (eauCaptee, mm)

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    # ! correction as broadcasting on xarray seems less constrained than on numpy
    # group 9
    #! replacing eauCaptee by water_gathered_by_mulch
    #! replacing stockMc by mulch_water_stock
    #// data["stockMc"][j:,:,:] = (data["stockMc"][j,:,:] + data["eauCaptee"][j,:,:]) # //[...,np.newaxis]
    data["mulch_water_stock"][j:,:,:] = (data["mulch_water_stock"][j,:,:] + data["water_gathered_by_mulch"][j,:,:]) # //[...,np.newaxis]
    
    return data



def RempliMc(j, data, paramITK):

    """
    Translated from the procedure PluieIrrig, of the original Pascal codes
    bileau.pas and exmodules2.pas

    wrapper function,
    updates water_gathered_by_mulch, eauDispo, and mulch_water_stock

    For more details, it is advised to refer to the works of Eric Scopel (UR
    AIDA), and the PhD dissertation of Fernando Maceina. 

    Notes from CB, 2014 :

    Hypotheses :
    A chaque pluie, on estime la quantité d'eau pour saturer le couvert. On la
    retire à l'eauDispo (pluie + irrig). On calcule la capacité maximum de
    stockage fonction de la biomasse et du taux de saturation rapportée en mm
    (humSatMc en kg H2O/kg de biomasse).
    La pluie est en mm :
    1 mm = 1 litre d'eau / m2
    1 mm = 10 tonnes d'eau / hectare = 10 000 kg/ha
    La biomasse est en kg/ha pour se rapporter à la quantité de pluie captée en
    mm Kg H2O/kg Kg/ha et kg/m2 on divise par 10 000 (pour 3000 kg/ha à humSat
    2.8 kg H2O/kg on a un stockage max de 0.84 mm de pluie !?) Cette capacité à
    capter est fonction du taux de couverture du sol calculé comme le LTR SurfMc
    est spécifié en ha/t (0.39), on rapporte en ha/kg en divisant par 1000 On
    retire alors les mm d'eau captées à la pluie incidente. Le ruisselement est
    ensuite calculé avec l'effet de contrainte du mulch

    group 10
    """

    data = estimate_water_captured_by_mulch(j, data, paramITK)
    data = update_available_water_after_mulch_filling(j, data)
    data = update_mulch_water_stock(j, data)

    return data


def estimate_runoff(j, data):
    """
    Evaluation of runoff ("lame de ruissellement", lr, mm) :
    
    If the quantity of rain (mm) is above the runoff threshold (seuilRuiss,
    mm), runoff is computed as the difference between the available water
    (eauDispo, mm) and the runoff threshold (seuilRuiss, mm) multiplied by
    the runoff percentage (pourcRuiss, %). Else, runoff value is set to 0.

    seuiRuiss and pourcRuiss are defined in load_iSDA_soil_data
    
    Question : should runoff be computed taking in consideration water captured by
    mulch to account for mulch effect on runoff mitigation ?

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    
    # group 11
    data["lr"][j,:,:] = xr.where(
        data["rain"][j,:,:] > data["seuilRuiss"],
        (data["eauDispo"][j,:,:]  - data["seuilRuiss"]) * data["pourcRuiss"],
        0,
    )

    return data


def update_available_water_after_runoff(j, data):
    """
    Updating available water (eauDispo, mm) :
    
    The available water is updated by subtracting the runoff (lr, mm) from the
    total available water (eauDispo, mm). This value is broadcasted onto the
    days axis.
    Args:
        j (_type_): _description_
        data (_type_): _description_
    """

    # group 12
    data["eauDispo"][j:,:,:] = (data["eauDispo"][j,:,:] - data["lr"][j,:,:])
    return data




def EvalRunOff(j, data, paramTypeSol):
    """
    Translated from the procedure PluieIrrig, of the original Pascal codes
    bileau.pas, exmodules1.pas and exmodules2.pas

    Notes from CB, 2014 :
    On a regroupé avant la pluie et l'irrigation (a cause de l'effet Mulch)
    si mulch on a enlevé l'eau captée
    oN CALCUL SIMPLEMENT LE RUISSELLEMENT EN FN DE SEUILS

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramTypeSol (_type_): _description_

    Returns:
        _type_: _description_
    """

    data = estimate_runoff(j, data)
    data = update_available_water_after_runoff(j, data)

    return data






def EvolRurCstr2(j, data, paramITK):

    """
    Translated from the procedure PluieIrrig, of the original Pascal codes
    bileau.pas

    Notes from CB, 10/06/2015 :
    Stress trop fort enracinement
    Trop d'effet de stress en tout début de croissance :
    1) la plantule a des réserves et favorise l'enracinement
    2) dynamique spécifique sur le réservoir de surface
    Cet effet stress sur l'enracinement ne s'applique que quand l'enracinement
    est supérieur é la profondeur du réservoir de surface. Effet stres a un
    effet sur la vitesse de prof d'enracinement au dessus d'un certain seuil de
    cstr (on augmente le cstr de 0.3 pour que sa contrainte soit affaiblie sur
    la vitesse) La vitesse d'enracinement potentielle de la plante peut etre
    bloque par manque d'eau en profondeur (Hum). La profondeur d'humectation est
    convertie en quantite d'eau maximum equivalente

    IN:
    Vrac : mm (en mm/jour) : Vitesse racinaire journalière §§ Daily root depth
    Hum : mm Quantité d'eau maximum jusqu'au front d'humectation §§ Maximum
    water capacity to humectation front
    StRuSurf : mm
    RU : mm/m
    RuSurf : mm/m

    INOUT:
    stRurMax : mm ==== ruRac
    stRur : mm ==== stockRac

    NB : on remet le nom de variables de CB plutôt que celles utilisées par MC dans le code Java
    """

    # ! dayvrac et deltarur reset à chaque itération ; on traine donc le j sur les autres variables

    # updating stRurMax, step 1 :
    #
    # stRurMax, also called ruRac in some versions of the model, is the maximum
    # root water storage capacity, aka Water column that can potentially be
    # strored in soil volume explored by root system.
    #
    # At the phase change between phases 0 and 1 (initialisation), the maximum
    # root water storage is initialised by multiplying the initial root depth
    # (profRacIni, mm) with the soil water storage capacity (ru, mm/m). This
    # value is broadcasted on the time series. For every other day in the cycle,
    # the value remains unchanged.

    #! renaming stRurMax to root_tank_capacity
    # group 14
    #// data["stRurMax"][j:,:,:] = np.where(
    data["root_tank_capacity"][j:,:,:] = np.where(
        (data["changePhase"][j,:,:] == 1) & (data["numPhase"][j,:,:] == 1),
        paramITK["profRacIni"] / 1000 * data["ru"],
        #// data["stRurMax"][j,:,:],
        data["root_tank_capacity"][j,:,:],
    )


    # updating dayVrac (daily variation in water height accessed by roots,
    # mm/day) :
    # 
    # At the day of phase change, for phases strictly above 1, and for which
    # maximum root water storage capacity (stRurMax) is greater than ruSurf
    # (maximum water storage capacity of the surface reservoir), the daily
    # variation in water height accessed by roots (dayVrac) is computed as the
    # product of the root growth speed (vRac, mm/day) and a coefficient. The
    # coefficient is computed as the drought stress coefficient (cstr) plus 0.3,
    # with a maximum bound of 1.0. It is thus modulated by drought stress. That
    # is to say, when the root has a maximum root water storage capacity above
    # the maximum water storage capacity of the surface reservoir, the root
    # growth speed is modulated by drought stress.
    #
    # ? Why is dayVrac in this case bounded in [0.3, 1] ?
    # According to CB, this is based on the hypothesis that during a drought
    # stress, the plant will preferably grow roots. Furthermore, using the [0.3,
    # 1] bound is a way to tell that up to a cstr of 0.7 there is no effect of
    # drought stress on the root growth speed.
    #
    # At the day of phase change, for phases strictly above 1, and for which
    # stRurMax is NOT greater than ruSurf, dayVrac is computed as the product of
    # the root growth speed (vRac, mm/day) and ru (mm/m).
    # 
    # Every other day, dayVrac is unchanged.

    # group 15  
    # ! simplified conditions
    # // condition = (data["numPhase"][j,:,:] > 0) & \
    # //       np.invert((data["numPhase"][j,:,:] == 1) & (data["changePhase"][j,:,:] == 1))
    condition = (data["numPhase"][j,:,:] > 1) & (data["changePhase"][j,:,:] == 1)

    #! renaming dayVrac to delta_root_tank_capacity
    #// data["dayVrac"][j,:,:] = np.where(
    data["delta_root_tank_capacity"][j,:,:] = np.where(
        condition,
        np.where(
            #! renaming stRurMax to root_tank_capacity
            #! renaming ruSurf to surface_tank_capacity
            #// (data["stRurMax"][j,:,:] > data["ruSurf"][j,:,:]),
            (data["root_tank_capacity"][j,:,:] > data["surface_tank_capacity"]),
            (data["vRac"][j,:,:] * np.minimum(data["cstr"][j,:,:] + 0.3, 1.0)) / 1000 * data["ru"],
            data["vRac"][j,:,:] / 1000 * data["ru"],
        ),
        #// data["dayVrac"][j,:,:],
        data["delta_root_tank_capacity"][j,:,:],
    )

    
    # updating deltaRur (change in root water storage capacity, mm) : 
    #
    # At the day of phase change, for phases strictly above 1, and for which the
    # difference between the humectation front (hum, mm) and the maximum root
    # water storage capacity (stRurMax, mm) is less than the daily variation in
    # water height accessed by roots (dayVrac, mm/day), the change in root water
    # storage capacity (deltaRur) is computed as the difference between the
    # humectation front and the maximum root water storage capacity. That is to
    # say that change in root water storage capacity is limited by the
    # humectation front.
    # 
    # At the day of phase change, for phases strictly above 1, and for which the
    # difference between the humectation front (hum, mm) and the maximum root
    # water storage capacity (stRurMax, mm) is NOT LESS than the daily variation
    # in water height accessed by roots (dayVrac, mm/day), the change in root
    # water storage capacity (deltaRur) is computed as the daily variation in
    # water height accessed by roots (dayVrac, mm/day).
    # 
    # For any other day, the change in root water storage capacity (deltaRur) is
    # unchanged.

    # group 16
    # ! simplified conditions
    # // condition = (data["numPhase"][j,:,:] > 0) & \
    # //       np.invert((data["numPhase"][j,:,:] == 1) & (data["changePhase"][j,:,:] == 1))
    condition = (data["numPhase"][j,:,:] > 1) & (data["changePhase"][j,:,:] == 1)

    #! renaming deltaRur with delta_root_tank_capacity
    #// data["deltaRur"][j:,:,:] = np.where(
    data["delta_root_tank_capacity"][j:,:,:] = np.where(
        condition,   
        np.where(
            #! renaming stRurMax to root_tank_capacity
            #! renaming dayVrac to delta_root_tank_capacity
            #// (data["hum"][j,:,:] - data["stRurMax"][j,:,:]) < data["dayVrac"][j,:,:],
            (data["hum"][j,:,:] - data["root_tank_capacity"][j,:,:]) < data["delta_root_tank_capacity"][j,:,:],
            #// data["hum"][j,:,:] - data["stRurMax"][j,:,:],
            data["hum"][j,:,:] - data["root_tank_capacity"][j,:,:],
            #! renaming dayVrac to delta_root_tank_capacity
            #// data["dayVrac"][j,:,:],
            data["delta_root_tank_capacity"][j,:,:],
        ),
        #// data["deltaRur"][j,:,:],
        data["delta_root_tank_capacity"][j,:,:],
    )


    # updating stRurMax/ruRac, step 2 :
    # 
    # At the day of phase change, for phases strictly above 1, the maximum root
    # water storage capacity (stRurMax, mm) is updated to be summed with the change
    # in root water storage capacity (deltaRur, mm). That is to say that the maximum
    # root water storage capacity is incremented by the change in root water
    # storage capacity.
    # 
    # stRurMax value is broadcasted 

    # group 17
    # ! simplified conditions
    # // data["stRurMax"][j:,:,:] = np.where(
    # //     (data["numPhase"][j,:,:] > 0),
    # //     np.where(
    # //         np.invert((data["changePhase"][j,:,:] == 1) & (data["numPhase"][j,:,:] == 1)),
    # //         data["stRurMax"][j,:,:] + data["deltaRur"][j,:,:],
    # //         data["stRurMax"][j,:,:],
    # //     ),
    # //     data["stRurMax"][j,:,:],
    # // )#[...,np.newaxis]
    #! renaming stRurMax to root_tank_capacity
    #! renaming deltaRur to delta_root_tank_capacity
    #// data["stRurMax"][j:,:,:] = np.where(
    data["root_tank_capacity"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] > 1) & (data["changePhase"][j,:,:] == 1),
        #// data["stRurMax"][j,:,:] + data["deltaRur"][j,:,:],
        data["root_tank_capacity"][j,:,:] + data["delta_root_tank_capacity"][j,:,:],
        #// data["stRurMax"][j,:,:],
        data["root_tank_capacity"][j,:,:],
    )

    
    # updating stRur/stockrac :
    #
    # At the day of phase change, for phases strictly above 1, and for which the
    # the maximum root water storage capacity (stRurMax, mm) is above the
    # surface water storage capacity (ruSurf, mm) (meaning that roots go beyond
    # the surface water storage capacity), the root water storage capacity
    # (stRur, mm) is incremented by the change in root water storage capacity
    # (deltaRur, mm).
    # 
    # However, if the maximum root water storage capacity (stRurMax, mm) is
    # BELOW the surface water storage capacity (ruSurf, mm) (meaning that roots
    # stay within the surface water storage capacity), the root water storage
    # capacity (stRur, mm) is updated to be equal to the stRuSurf (mm) minus
    # 1/10th of the surface water storage capacity (ruSurf, mm),  multiplied by
    # the ratio between the maximum root water storage capacity (stRurMax, mm)
    # and the surface water storage capacity (ruSurf, mm). That is to say "we
    # take at the prorata of depth and surface stock"
    #
    # For any other day, the root water storage capacity (stRur, mm) is
    # unchanged.
    #
    # stRur value is broadcasted

    # group 18
    # ! simplified conditions
    # // condition = (data["numPhase"][j,:,:] > 0) & np.invert((data["changePhase"][j,:,:] == 1) & (data["numPhase"][j,:,:] == 1)),
    condition = (data["numPhase"][j,:,:] > 1) & (data["changePhase"][j,:,:] == 1),
    
    #! renaming stRur to root_tank_stock
    #// data["stRur"][j:,:,:] = np.where(
    data["root_tank_stock"][j:,:,:] = np.where(
        condition,
        np.where(
            #! renaming stRurMax to root_tank_capacity
            #! renaming ruSurf to surface_tank_capacity
            #// (data["stRurMax"][j,:,:] > data["ruSurf"][j,:,:]),
            (data["root_tank_capacity"][j,:,:] > data["surface_tank_capacity"]),
            #! renaming stRur to root_tank_stock
            #! renaming deltaRur to delta_root_tank_capacity
            #// data["stRur"][j,:,:] + data["deltaRur"][j,:,:],
            data["root_tank_stock"][j,:,:] + data["delta_root_tank_capacity"][j,:,:],
            #! renaming stRur to root_tank_stock
            #! renaming stRuSurf to surface_tank_stock
            #// np.maximum((data["stRuSurf"][j,:,:] - data["ruSurf"][j,:,:] * 1/10) * (data["stRurMax"][j,:,:] / data["ruSurf"][j,:,:]), 0),
            np.maximum((data["surface_tank_stock"][j,:,:] - data["surface_tank_capacity"] * 1/10) * (data["root_tank_capacity"][j,:,:] / data["surface_tank_capacity"]), 0),
        ),  
        #! renaming stRur to root_tank_stock
        #// data["stRur"][j,:,:],
        data["root_tank_stock"][j,:,:],
    )
    

    return data




# bhytypeFAO, ***bileau***; exmodules 1 & 2, risocas ###trad OK

def rempliRes(j, data):

    # TODO: modify positions of i indexers to suit the new data structure
    """
    Translated from the procedure rempliRes, of the original Pascal codes
    bileau.pas

    Main hypotheses : 
    - the water dynamics is represented by a filling from the top and an evolution 
    of the reservoirs sizes when the filling is above the maximum quantity of the
    current size (humectation front).
    - when the maximum size is reached by filling, it is considered as drainage.
    - inside a reservoir, water is distributed homogeneously (may be considered
    valid up to 2m depth, according to CB, from other sources).

    3 reservoirs are represented:
    1) a global reservoir, evolving in depth according to the humectation front
    2) a surface reservoir (fixed size) where evaporation and a part of the
    transpiration occurs when roots are present
    3) a root reservoir, evolving according to the root front (when roots are
    present)

    REMARK : these reservoirs overlap, and instead of managing depths, we manage water stocks



    Notes from CB, 10/06/2015 :
    prise en compte de stock d'eau résilient pour les simulation continues
    Hypothèse de la MAJ des stock en fn de l'eau r�siliente de l'ann�e pr�c�dente
    dans le cas des simulations pluri annuelle en continue (NbAn = 1):
    A la r�colte on recup�re les stock d'eau (StRuPrec), la prof d'Humectation (Humprec)
    et la prof d'enracinement (stRurMaxprec). Pour le reservoir de surface on ne change rien.
    On MAJ le stRu avec le stock de surface stRuSurf, Hum avec le max de remplissage de surface (RuSurf)
    Si le StRu avec l'apport d'eau devinet sup au Hum
    alors on tient compte dans cette augmentation du stock r�silient avec deux cas possible :
    Si StRu est < � stRurMaxprec
    alors on ajoute l'eau r�siliente contenue dans l'ancienne zone racinaire en fn
    de la diff�rence de stock
    Sinon on a de l'eau r�siliente au maximum de la CC jusqu'� l'ancienne HumPrec,
    on rempli alors StRu de la diff�rence etre ces deux valeurs puis on fait la MAJ
    des Dr, StRur, Hum etc...
    """


    # updating variables at the end of the growing cycle

    condition = (data["numPhase"][j,:,:] == 7) & (data["changePhase"][j,:,:] == 1)

    # when the phase changes from 7 to 1, the humPrec (mm, previous maximum
    # water capacity to humectation front) is set to equal the higher value
    # between hum (mm, maximum water capacity to humectation front) and the root
    # water storage capacity (stRur, mm).
    # group 20
    data["humPrec"][j:,:,:] = np.where(
        condition,
        #! renaming ruSurf to surface_tank_capacity
        #// np.maximum(data["hum"][j,:,:], data["ruSurf"][j,:,:]),
        np.maximum(data["hum"][j,:,:], data["surface_tank_capacity"]),
        data["humPrec"][j,:,:],
    )

    
    # when the phase changes from 7 to 1, the hum (mm, maximum water capacity to
    # humectation front) is set to equal the ruSurf (mm, maximum water storage
    # capacity of the surface reservoir)
    # group 21
    data["hum"][j:,:,:] = np.where(
        condition,
        #! renaming ruSurf to surface_tank_capacity
        #// data["ruSurf"][j,:,:],
        data["surface_tank_capacity"],
        data["hum"][j,:,:],
    )


    # when the phase changes from 7 to 1, the stRurMaxPrec (mm, previous maximum
    # water capacity to root front) is set to equal stRurMax (mm, maximum water
    # capacity to root front)
    # group 22
    data["stRurMaxPrec"][j:,:,:] = np.where(
        condition,
        #! renaming stRurMax to root_tank_capacity
        #// data["stRurMax"][j,:,:],
        data["root_tank_capacity"],
        data["stRurMaxPrec"][j,:,:],
    )


    # when the phase changes from 7 to 1, the stRurPrec (mm, previous water
    # storage capacity of the root reservoir) is set to equal stRur/stRurMax,
    # that is to say the ratio of the water storage capacity of the root
    # reservoir
    # group 23
    data["stRurPrec"][j:,:,:] = np.where(
        condition,
        #! renaming stRur to root_tank_stock
        #! renaming stRurMax to root_tank_capacity
        #// data["stRur"][j,:,:]/data["stRurMax"][j,:,:],
        data["root_tank_stock"][j,:,:]/data["root_tank_capacity"][j,:,:],
        data["stRurPrec"][j,:,:],
    )


    # when the phase changes from 7 to 1, the stRuPrec (mm, previous water
    # storage capacity of the global reservoir) is set to equal the differe,ce
    # between stTot (mm, total water storage capacity of the global reservoir)
    # and stRurSurf (mm, water storage capacity of the surface reservoir)
    # group 24
    #! stRurSurf is not defined... we may want to drop this group
    data["stRuPrec"][j:,:,:] = np.where(
        condition,
        #! renaming stTot to total_tank_stock
        #// data["stRu"][j,:,:] - data["stRurSurf"][j,:,:],
        data["total_tank_stock"][j,:,:] - data["stRurSurf"][j,:,:], # essai stTot
        data["stRuPrec"][j,:,:],
    )







    # updating stRuMax :
    #
    # stRuMax is the max water storage capacity of the global reservoir ; it is
    # redfined at each loop as the product of the water storage capacity
    # (réserve utile, mm/m if soil) and the maximum depth of soil N.B. : on code
    # version 10/06/2015, resilience of water stock for multi-annual simulations
    # was been implemented
    #? where is it now ? why redfining stRuMax at each loop ? neither ru, profRu
    #? nor stRuMax seem to change during the simulation
    # group 25
    data["stRuMax"][j:,:,:] = (data["ru"] * data["profRu"] / 1000) #.copy()#[...,np.newaxis]
    

    # updating stRuSurfPrec :
    #
    # stRuSurf is the water stock in the surface reservoir. here, we save the
    # previous value of stRuSurf before doing any update
    #? this has little sense, as previous value of stRuSurf is stored at the ?
    #? (i-1)-th position in the xarray dataarray
    # group 26 
    #! after replacing data["stRuSurfPrec"][j,:,:] by data["stRuSurf"][j-1,:,:]
    #! in group 28, we can safely remove the use of stRuSurfPrec
    #// data["stRuSurfPrec"][j,:,:] = data["stRuSurf"][j,:,:].copy()
    

    # updating stRuSurf :
    #
    # we update stRuSurf (mm, water stock in the surface reservoir) by adding
    # the eauDispo, which as this point is the water available from rain and
    # irrigation for the day after estimation of intake by mulch, and runoff.
    # however, we do not allow stRuSurf to exceed 110% of the ruSurf (mm,
    # maximum water storage capacity of the surface reservoir)
    # group 27
    #! renaming stRuSurf to surface_tank_stock
    #// data["stRuSurf"][j:,:,:] = np.minimum(
    data["surface_tank_stock"][j:,:,:] = np.minimum(
        #// data["stRuSurf"][j,:,:] + data["eauDispo"][j,:,:],
        data["surface_tank_stock"][j,:,:] + data["eauDispo"][j,:,:],
        #! renaming ruSurf to surface_tank_capacity
        #// 1.1 * data["ruSurf"][j,:,:]
        1.1 * data["surface_tank_capacity"]
    )


    # updating eauTranspi : estimation of transpirable water
    #
    # eauTranspi (mm, water transpirable) is the water available for
    # transpiration from the surface reservoir.
    # If the stock of surface reservoir is lower than 10% of the maximum water
    # storage capacity of the surface reservoir, the water available for
    # transpiration is the water available for the day (eauDispo), minus the
    # difference between 1/10th of the maximum water storage capacity of the
    # surface reservoir and the stock of surface reservoir, bounded by 0. Said
    # otherwise, a part of the water available for the day is considered as
    # linked to the surface reservoir.
    # Otherwise, the water available for transpiration is equal to the water
    # available for the day (eauDispo).
    #? here we use the stRuSurf value at indice j-1 because we want to use the
    #? values before their update in group 27 ; instead it may be clever to move
    #? this group before group 27 so we remove the j-1 indices
    # group 28
    data["eauTranspi"][j:,:,:] = np.where(
        # ! modifying to replace stRuSurfPrec by stRuSurf
        #! renaming ruSurf to surface_tank_capacity
        #! renaming stRuSurfPrec to surface_tank_stock
        # // data["stRuSurfPrec"][j,:,:] < data["ruSurf"][j,:,:]/10,
        data["surface_tank_stock"][j-1,:,:] < data["surface_tank_capacity"] * 0.1,
        np.maximum(
            0,
            # ! modifying to replace stRuSurfPrec by stRuSurf
            #! renaming ruSurf to surface_tank_capacity
            #! renaming stRuSurf to surface_tank_stock
            # //data["eauDispo"][j,:,:] - (data["ruSurf"][j,:,:]/10 - data["stRuSurfPrec"][j,:,:])
            data["eauDispo"][j,:,:] - (data["surface_tank_capacity"] * 0.1 - data["surface_tank_stock"][j-1,:,:])
            ),
        data["eauDispo"][j,:,:],
    )



    # updating stTot, step 1 :
    #
    # stTot, also known as stRu in some versions of the model; is the water
    # stock of the global reservoir. Here, we increment stTot by the quantity of
    # transpirable water.
    #? why incrementing stTot by eauTranspi ? eauTranspi is not intended to be
    #? transpired...?
    # group 29
    #! renaming stTot with total_tank_stock
    #// data["stTot"][j:,:,:] = (data["stTot"][j,:,:] + data["eauTranspi"][j,:,:]).copy()#[...,np.newaxis]
    data["total_tank_stock"][j:,:,:] = (data["total_tank_stock"][j,:,:] + data["eauTranspi"][j,:,:]).copy()


    # defining stRuVar :
    #
    # stRuVar is the difference between the total water stock (stTot) and stRuPrec (mm, the prvious water stock of the global reservoir), bounded by 0.
    #? we may want to rename stRuPrec to stTotPrec, or use stTot with another notation
    #? stRuPrec is updated in group 24

    # modif 10/06/2015 Resilience stock eau cas simul pluri en continue
    # différence entre stock total et stRuPrec (non défini clairement ?), borné au minimum en 0
    # group 30
    #! we propose a different version based on stTot
    #! renaming stTot to total_tank_stock
    #// data["stRuVar"][j:,:,:] = np.maximum(0, data["stTot"][j,:,:] - data["stRuPrec"][j,:,:])[...,np.newaxis]
    data["stRuVar"][j:,:,:] = np.maximum(0, data["total_tank_stock"][j,:,:] - data["total_tank_stock"][j-1,:,:])






    condition_1 = (data["stRuVar"][j,:,:] > data["hum"][j,:,:])
    #! we replace stRurMaxPrec by stRurMax with indice j-1
    #! renaming stRurMax with root_tank_capacity
    #// condition_2 = (data["hum"][j,:,:] <= data["stRurMaxPrec"][j,:,:])
    condition_2 = (data["hum"][j,:,:] <= data["root_tank_capacity"][j-1,:,:])
    #! we replace humPrec by hum with indice j-1
    #// condition_3 = (data["hum"][j,:,:] < data["humPrec"][j,:,:])
    condition_3 = (data["hum"][j,:,:] < data["hum"][j-1,:,:])

    # updating stTot step 1
    #
    # stTot, also known as stRu in some versions of the model, is the water stock of the global reservoir.
    # if the variation in total water stock (stRuVar) is greater than the maximum water quantity until the humidity front (hum),
    # and if the quantity of water until the humidity front is equal or less than the maximum root water stock (stRurMax) at j-1,
    # the total water stock is incremented by the difference between stRuVar and hum, multiplied by the previous root water stock (stRurPrec).
    #
    # if the variation in total water stock (stRuVar) is greater than the maximum water quantity until the humidity front (hum),
    # and if the quantity of water until the humidity front is MORE than the maximum root water stock (stRurMax) at j-1,
    # then if the humidity front is lower than the previous humidity front, stTot taks stRuVar as value.
    # Otherwise, its value does not change 
    # group 31
    #! renaming stTot to total_tank_stock
    #// data["stTot"][j:,:,:] = np.where(
    data["total_tank_stock"][j:,:,:] = np.where(
        condition_1,
        np.where(
            condition_2,
            #! we replace stRurPrec with stRur at indice j-1
            #! renaming stRur to root_tank_stock
            #! renaming stTot to total_tank_stock
            #// data["stTot"][j,:,:] + (data["stRuVar"][j,:,:] - data["hum"][j,:,:]) * data["stRurPrec"][j,:,:],
            data["total_tank_stock"][j,:,:] + (data["stRuVar"][j,:,:] - data["hum"][j,:,:]) * data["root_tank_stock"][j-1,:,:],
            np.where(
                condition_3,
                data["stRuVar"][j,:,:],
                #! renaming stTot to total_tank_stock
                #// data["stTot"][j,:,:],
                data["total_tank_stock"][j,:,:],
            ),
        ),
        #! renaming stTot to total_tank_stock  
        #// data["stTot"][j,:,:],
        data["total_tank_stock"][j,:,:],
    )



    # group 32
    data["stRuPrec"][j:,:,:] = np.where(
        condition_1,
        np.where(
            condition_2,
            np.maximum(0, data["stRuPrec"][j,:,:] - (data["stRuVar"][j,:,:] - data["hum"][j,:,:]) * data["stRurPrec"][j,:,:]),
            np.where(
                condition_3,
                0,
                data["stRuPrec"][j,:,:],
            ),
        ),
        data["stRuPrec"][j,:,:],
    )



    # condition_1 = (data["stRuVar"][j,:,:] > data["hum"][j,:,:])
    # condition_2 = (data["hum"][j,:,:] <= data["stRurMaxPrec"][j,:,:])
    # condition_3 = (data["hum"][j,:,:] < data["humPrec"][j,:,:])


    # groupe 33
    data["stRuVar"][j:,:,:] = np.where(
        condition_1,
        np.where(
            condition_2,
            data["stRuVar"][j,:,:] + (data["stRuVar"][j,:,:] - data["hum"][j,:,:]) * data["stRurPrec"][j,:,:],
            np.where(
                condition_3,
                data["stRuVar"][j,:,:] + data["stRuPrec"][j,:,:],
                data["stRuVar"][j,:,:],
            ),
        ),
        data["stRuVar"][j,:,:],
    )

    # hum
    # front d'humectation mis à jour sur la base du delta maximal de stock d'eau total
    # dans l'intervalle [stRuVar, stRuMax]
    # modif 10/06/2015 Resilience stock eau cas simul pluri en continue
    # modif 27/07/2016 Hum ne peut �tre au dessus de stRu (stocktotal)
    # groupe 34
    data["hum"][j:,:,:] = np.maximum(data["stRuVar"][j,:,:], data["hum"][j,:,:])#[...,np.newaxis]
    # groupe 35
    data["hum"][j:,:,:] = np.minimum(data["stRuMax"][j,:,:], data["hum"][j,:,:])#[...,np.newaxis]


    #! renaming stTot to total_tank_stock
    #// condition = (data["stTot"][j,:,:] > data["stRuMax"][j,:,:])
    condition = (data["total_tank_stock"][j,:,:] > data["stRuMax"][j,:,:])

    # groupe 36
    # essais stTot
    data["dr"][j,:,:] = np.where(
        condition,
        #! renaming stTot to total_tank_stock
        #// data["stRu"][j,:,:] - data["stRuMax"][j,:,:],
        data["total_tank_stock"][j,:,:] - data["stRuMax"][j,:,:],
        0,
    )

    # groupe 37
    # essais stTot
    #! renaming stTot to total_tank_stock
    #// data["stRu"][j,:,:] = np.where(
    #// data["stTot"][j:,:,:] = np.where(   
    data["total_tank_stock"][j:,:,:] = np.where(  
        condition,
        data["stRuMax"][j,:,:],
        # data["stRu"][j,:,:],
        #// data["stTot"][j,:,:],
        data["total_tank_stock"][j,:,:],
    )#[...,np.newaxis]


    # groupe 38
    # // avant modif 10/06/2015
    # data["hum"][j:,:,:] = np.maximum(data["hum"][j,:,:], data["stRu"][j,:,:])
    # essais stTot
    #! renaming stTot to total_tank_stock
    #// data["hum"][j:,:,:] = np.maximum(data["hum"][j,:,:], data["stTot"][j,:,:])[...,np.newaxis]
    data["hum"][j:,:,:] = np.maximum(data["hum"][j,:,:], data["total_tank_stock"][j,:,:])#[...,np.newaxis]
    #! en conflit avec le calcul précédent de hum

    # groupe 39
    # Rempli res racines
    #! renaming stRur to root_tank_stock
    #! renaming stRurMax to root_tank_capacity
    #// data["stRur"][j:,:,:] = np.minimum(data["stRur"][j,:,:] + data["eauTranspi"][j,:,:], data["stRurMax"][j,:,:])[...,np.newaxis]
    data["root_tank_stock"][j:,:,:] = np.minimum(data["root_tank_stock"][j,:,:] + data["eauTranspi"][j,:,:], data["root_tank_capacity"][j,:,:])#[...,np.newaxis]

    # groupe 40
    # essais stTot
    #! renaming stRur to root_tank_stock
    #! renaming stTot to total_tank_stock
    #// data["stRur"][j,:,:] = np.minimum(data["stRur"][j,:,:], data["stRu"][j,:,:])
    data["root_tank_stock"][j:,:,:] = np.minimum(data["root_tank_stock"][j,:,:], data["total_tank_stock"][j,:,:])#[...,np.newaxis]

    

    return data


def rempliRes_alt(j, data):


   


    # stRuMax
    # stock d'eau maximal dans la réserve utile ; capacité maximale de la réserve utile
    # redéfinie à chaque boucle comme étant le produit de la réserve utile (mm/m de sol) et 
    # de la profondeur maximale de sol
    # modif 10/06/2015 Resilience stock eau cas simul pluri en continue
    data["stRuMax"][j:,:,:] = (data["ru"][j,:,:] * data["profRu"][j,:,:] / 1000).copy()
    
    # stRuSurfPrec
    # Rempli Res surface
    # on enregistre le stock d'eau de surface précédent 
    data["stRuSurfPrec"][j,:,:] = data["stRuSurf"][j,:,:].copy()
    
    # stRuSurf
    # on met à jour le stock d'eau en surface pour qu'il corresponde au stock de surface incrémenté
    # de la valeur d'eau disponible eauDispo ; 
    # on borne cependant cette valeur à 110% de la réserve utile de surface.
    data["stRuSurf"][j:,:,:] = np.minimum(
        data["stRuSurf"][j,:,:] + data["eauDispo"][j,:,:],
        data["ruSurf"][j,:,:] + data["ruSurf"][j,:,:] / 10
    )

    # eauTranspi
    # quantité d'eau transpirable
    # si le stock de surface avant mise à jour est inférieur à 10% de la réserve utile de surface, 
    # la quantité d'eau transpirable correspond à l'apport d'eau du jour (eauDispo), moins la différence 
    # entre 1/10e de la réserve utile de surface et le stock de surface avant mise à jour, bornée au minimum par 0,
    # (autrement dit, une partie de l'apport d'eau du jour est considérée comme liée au réservoir de surface)
    # sinon la quantité d'eau transpirable est égale à l'apport d'eau du jour (eauDispo)
    data["eauTranspi"][j:,:,:] = np.where(
        data["stRuSurfPrec"][j,:,:] < data["ruSurf"][j,:,:]/10,
        np.maximum(
            0,
            data["eauDispo"][j,:,:] - (data["ruSurf"][j,:,:]/10 - data["stRuSurfPrec"][j,:,:])
            ),
        data["eauDispo"][j,:,:],
    )



    # stRu/stTot étape 1
    # stock d'eau total sur l'ensemble du réservoir
    # on incrémente le stock d'eau total de la quantité d'eau transpirable
    data["stTot"][j:,:,:] = (data["stTot"][j,:,:] + data["eauTranspi"][j,:,:]).copy() ## ok




    condition = (data["stTot"][j,:,:] > data["stRuMax"][j,:,:])

    # essais stTot
    data["dr"][j,:,:] = np.where(
        condition,
        # data["stRu"][j,:,:] - data["stRuMax"][j,:,:],
        data["stTot"][j,:,:] - data["stRuMax"][j,:,:],
        0,
    )

    # essais stTot
    # data["stRu"][j,:,:] = np.where(
    data["stTot"][j:,:,:] = np.where(   
        condition,
        data["stRuMax"][j,:,:],
        # data["stRu"][j,:,:],
        data["stTot"][j,:,:],
    )



    data["hum"][j:,:,:] = np.maximum(data["hum"][j,:,:], data["stTot"][j,:,:])

    data["stRur"][j:,:,:] = np.minimum(data["stRur"][j,:,:] + data["eauTranspi"][j,:,:], data["stRurMax"][j,:,:])
    data["stRur"][j:,:,:] = np.minimum(data["stRur"][j,:,:], data["stTot"][j,:,:])




    return data


def EvalFESW(j, data):
    """
    depuis bileau.pas

    Estimation de la fraction d'eau evaporable, rapporte donc au reservoir
    de surface, RuSurf est le stock d'eau maxi disponible pour la plante
    sur ce reservoir
    Modif : on considere que pour l'�vaporation la moitie de cette
    valeur doit etre ajout�e.
    // Parametres
    IN:
    StRusurf : mm
    RuSurf : mm
    OUT:
    fesw : mm
    """

    #! renaming stRuSurf to surface_tank_stock
    #! renaming ruSurf with surface_tank_capacity
    #// data["fesw"][j,:,:] = data["stRuSurf"][j,:,:] / (data["ruSurf"][j,:,:] + data["ruSurf"][j,:,:] / 10)
    data["fesw"][j,:,:] = data["surface_tank_stock"][j,:,:] / (data["surface_tank_capacity"] + data["surface_tank_capacity"] / 10)

    return data




def EvalKceMc(j, data, paramITK):
    """
    depuis bileau.pas
    
    Trois possibilit�s d'extinction sur l'�vaporation :
    ltr : couverture de la plante
    Mulch : effet couvrant permanent et constant; 100 pas de Mulch, 0 couvert complet bache)
    exp() �quivalent � formule de calcul du ltr mais appliqu� � l'effet couvrant d'un
    mulch couvert de paillis... �volutif    
    """

    # Kce := Mulch/100 * ltr * exp(-coefMc * SurfMc * BiomMc/1000);
    data["kce"][j,:,:] = paramITK["mulch"] / 100 * data["ltr"][j,:,:] * np.exp(-paramITK["coefMc"] * paramITK["surfMc"] * data["biomMc"][j,:,:]/1000)
    
    return data




def DemandeSol(j, data):
    """
    depuis bileau.pas

    Estimation de l'evaporation potentielle du sol, on ne tient pas
    compte d'une variation de l'evaporation en fonction d'une humectation
    differente entre le haut et le bas du reservoir, on a un parametre
    mulch qui peu traduire le phenomene d'auto mulching (defaut : 0.7)
    qui peu aussi traduire un mulch par couverture vegetale ou...
    La reduction de l'evaporation par l'evolution de la couverture
    du sol par la plante est traduit par ltr.

    // Parametres
    IN:
    ETo : mm
    Kce : %
    OUT:
    evapPot : mm
    """
    # group 44
    data["evapPot"][j:,:,:] = (data["ET0"][j,:,:] * data["kce"][j,:,:]).copy()#[...,np.newaxis]

    return data




def EvapMc(j, data, paramITK):
    """
    group 47
    depuis bileau.pas

    comme pour FESW on retire du stock la fraction evaporable
    la demande climatique étant réduite é la fraction touchant le sol ltr
    on borne é 0
    """
    # on doit reset FEMcW à chaque cycle ?
    # Var FEMcW : double;

    # group 45
    data["FEMcW"][j,:,:] = np.where(
        #! replacing stockMc with mulch_water_stock
        #// data["stockMc"][j,:,:] > 0,
        data["mulch_water_stock"][j,:,:] > 0,
        #// (paramITK["humSatMc"] * data["biomMc"][j,:,:] * 0.001) / data["stockMc"][j,:,:],
        (paramITK["humSatMc"] * data["biomMc"][j,:,:] * 0.001) / data["mulch_water_stock"][j,:,:],
        data["FEMcW"][j,:,:],
    )

    # group 46
    #! replacing stockMc with mulch_water_stock
    #// data["stockMc"][j:,:,:] = np.maximum(
    data["mulch_water_stock"][j:,:,:] = np.maximum(
        0,
        #// data["stockMc"][j,:,:] - data["ltr"][j,:,:] * data["ET0"][j,:,:] * data["FEMcW"][j,:,:]**2,
        data["mulch_water_stock"][j,:,:] - data["ltr"][j,:,:] * data["ET0"][j,:,:] * data["FEMcW"][j,:,:]**2,
    )#[...,np.newaxis]

    return data




def EvapRuSurf(j, data):
    """
    group 48
    depuis bileau.pas 

    Estimation de l'evaporation relle, rapporte a la fraction d'eau evaporable
    // Parametres
    IN:
    fesw : mm
    evapPot : mm
    stRuSurf : mm
    OUT:
    evap : mm
    """
    #! replacing stRuSurf by surface_tank_stock
    #// data["evap"][j:,:,:] = np.minimum(data["evapPot"][j,:,:] * data["fesw"][j,:,:]**2, data["stRuSurf"][j,:,:])[...,np.newaxis]
    data["evap"][j:,:,:] = np.minimum(data["evapPot"][j,:,:] * data["fesw"][j,:,:]**2, data["surface_tank_stock"][j,:,:])#[...,np.newaxis]

    return data





def EvalFTSW(j, data):
    """
    group 49
    depuis bileau.pas 

    Estimation de la fraction d'eau transpirable, rapporte donc au reservoir
    contenant les racines
    // Parametres
    IN:
    RuRac : mm
    StockRac : mm
    OUT:
    ftsw : mm
    """

    data["ftsw"][j:,:,:] = np.where(
        #! renaming stRurMax to root_tank_capacity
        #// data["stRurMax"][j,:,:] > 0,
        data["root_tank_capacity"][j,:,:] > 0,
        #! renaming stRur to root_tank_stock
        #! renaming stRurMax to root_tank_capacity
        #// data["stRur"][j,:,:] / data["stRurMax"][j,:,:],
        data["root_tank_stock"][j,:,:] / data["root_tank_capacity"][j,:,:],
        0,
    )#[...,np.newaxis]

    return data




def DemandePlante(j, data):
    # ggroup 51
    # d'près bileau.pas
    # TrPot := Kcp * ETo;
    # attention, séparation de ETp et ET0 dans les formules
    data["trPot"][j:,:,:] = (data["kcp"][j,:,:] * data["ET0"][j,:,:]).copy()#[...,np.newaxis]
    
    return data




def EvalKcTot(j, data):
    # group 52
    # d'après bileau.pas
    # added a condition on 19/08/22 to match SARRA-H original behavior
    data["kcTot"][j:,:,:] = np.where(
        data["kcp"][j,:,:] == 0.0,
        data["kce"][j,:,:],
        data["kce"][j,:,:] + data["kcp"][j,:,:],
    )#[...,np.newaxis]

    return data


def CstrPFactor(j, data, paramVariete):
    # group 57
    # d'après bileau.pas

    # group 53
    data["pFact"][j:,:,:] = paramVariete["PFactor"] + 0.04 * (5 - np.maximum(data["kcp"][j,:,:], 1) * data["ET0"][j,:,:])#[...,np.newaxis]

    # group 54
    data["pFact"][j:,:,:] = np.minimum(np.maximum(0.1, data["pFact"][j,:,:]), 0.8)#[...,np.newaxis]

    #group 55
    data["cstr"][j:,:,:] = np.minimum((data["ftsw"][j,:,:] / (1 - data["pFact"][j,:,:])), 1)#[...,np.newaxis]

    # group 56
    data["cstr"][j:,:,:] = np.maximum(0, data["cstr"][j,:,:])#[...,np.newaxis]

    return data




def EvalTranspi(j, data):
    # d'après bileau.pas
    # group 58
    data["tr"][j:,:,:] = (data["trPot"][j,:,:] * data["cstr"][j,:,:]).copy()#[...,np.newaxis]
    return data



def ConsoResSep(j, data):
    """
    d'après bileau.pas

    group 71

    Separation de tr et evap. Consommation de l'eau sur les reservoirs
    Hypothese : l'evaporation est le processus le plus rapide, retranche
    en premier sur le reservoir de surface. Comme reservoir de surface
    et reservoirs racinaires se chevauchent, il nous faut aussi calcule sur
    le reservoir ayant des racines la part deja extraite pour l'evaporation.
    Quand la profondeur des racines est inferieur au reservoir de surface
    on ne consomme en evaporation que la fraction correspondant a cette
    profondeur sur celle du reservoir de surface (consoRur).
    Les estimations d'evaporation et de transpirations sont effectues
    separemment, on peut ainsi avoir une consommation legerement superieure
    a l'eau disponible. On diminuera donc la transpiration en consequence.

    Modif : Pour les stock d'eau on tient compte de la partie rajoutee au
    reservoir de surface qui ne peut etre que evapore (air dry)
    // Parametres
    IN:
    stRurMax : mm
    RuSurf : mm
    evap : mm
    trPot : mm
    evaPot : mm
    INOUT :
    stRuSurf : mm
    tr : mm
    stRur : mm
    stRu : mm
    OUT:
    etr : mm
    etm : mm
    """

    # part transpirable sur le reservoir de surface
    # group 59
    #! replacing stRuSurf by surface_tank_stock
    #! renaming ruSurf with surface_tank_capacity
    #// data["trSurf"][j:,:,:] = np.maximum(0, data["stRuSurf"][j,:,:] - data["ruSurf"][j,:,:] / 10)[...,np.newaxis]
    data["trSurf"][j:,:,:] = np.maximum(0, data["surface_tank_stock"][j,:,:] - data["surface_tank_capacity"] / 10)#[...,np.newaxis]

    # qte d'eau evapore a consommer sur le reservoir de surface
    # group 60
    #! replacing stRuSurf by surface_tank_stock
    #// data["stRuSurf"][j:,:,:] = np.maximum(0, data["stRuSurf"][j,:,:] - data["evap"][j,:,:])[...,np.newaxis]
    data["surface_tank_stock"][j:,:,:] = np.maximum(0, data["surface_tank_stock"][j,:,:] - data["evap"][j,:,:])#[...,np.newaxis]


    # qte d'eau evapore a retirer sur la part transpirable
    # group 61
    data["consoRur"][j:,:,:] = np.where(
        data["evap"][j,:,:] > data["trSurf"][j,:,:],
        data["trSurf"][j,:,:],
        data["evap"][j,:,:],
    )#[...,np.newaxis]

    # data["stRu"][j:,:,:] = np.maximum(0, data["stRu"][j,:,:] - data["consoRur"][j,:,:])
    # essais stTot
    # group 62
    #! renaming stTot to total_tank_stock
    #// data["stTot"][j:,:,:] = np.maximum(0, data["stTot"][j,:,:] - data["consoRur"][j,:,:])[...,np.newaxis]
    data["total_tank_stock"][j:,:,:] = np.maximum(0, data["total_tank_stock"][j,:,:] - data["consoRur"][j,:,:])#[...,np.newaxis]

    #  fraction d'eau evapore sur la part transpirable qd les racines sont moins
    #  profondes que le reservoir de surface, mise a jour des stocks transpirables
    # group 63
    data["consoRur"][j:,:,:] = np.where(
        #! renaming stRurMax with root_tank_capacity
        #! renaming ruSurf with surface_tank_capacity
        #// data["stRurMax"][j,:,:] < data["ruSurf"][j,:,:],
        data["root_tank_capacity"] < data["surface_tank_capacity"],
        #! renaming stRur to root_tank_stock
        #! renaming ruSurf with surface_tank_capacity
        #// data["evap"][j,:,:] * data["stRur"][j,:,:] / data["ruSurf"][j,:,:],
        data["evap"][j,:,:] * data["root_tank_stock"][j,:,:] / data["surface_tank_capacity"],
        data["consoRur"][j,:,:],
    )#[...,np.newaxis]

    # group 64
    #! renaming stRur to root_tank_stock
    #// data["stRur"][j:,:,:] = np.maximum(0, data["stRur"][j,:,:] - data["consoRur"][j,:,:])#[...,np.newaxis]
    data["root_tank_stock"][j:,:,:] = np.maximum(0, data["root_tank_stock"][j,:,:] - data["consoRur"][j,:,:])#[...,np.newaxis]


    # // reajustement de la qte transpirable considerant que l'evap a eu lieu avant
    # // mise a jour des stocks transpirables  
    # group 65
    data["tr"][j:,:,:] = np.where(
        #! renaming stRur to root_tank_stock
        #// data["tr"][j,:,:] > data["stRur"][j,:,:],
        data["tr"][j,:,:] > data["root_tank_stock"][j,:,:],
        #// np.maximum(data["stRur"][j,:,:] - data["tr"][j,:,:], 0),
        np.maximum(data["root_tank_stock"][j,:,:] - data["tr"][j,:,:], 0),
        data["tr"][j,:,:],
    )#[...,np.newaxis]


    # group 66
    #! renaming stRuSurf with surface_tank_stock
    #// data["stRuSurf"][j:,:,:] = np.where(
    data["surface_tank_stock"][j:,:,:] = np.where(
        #! renaming stRur to surface_tank_stock
        #// data["stRur"][j,:,:] > 0,
        data["root_tank_stock"][j,:,:] > 0,
        #// np.maximum(data["stRuSurf"][j,:,:] - (data["tr"][j,:,:] * np.minimum(data["trSurf"][j,:,:]/data["stRur"][j,:,:], 1)), 0),
        #! renaming stRuSurf with surface_tank_stock
        #// np.maximum(data["stRuSurf"][j,:,:] - (data["tr"][j,:,:] * np.minimum(data["trSurf"][j,:,:]/data["root_tank_stock"][j,:,:], 1)), 0),
        np.maximum(data["surface_tank_stock"][j,:,:] - (data["tr"][j,:,:] * np.minimum(data["trSurf"][j,:,:]/data["root_tank_stock"][j,:,:], 1)), 0),
        #// data["stRuSurf"][j,:,:],
        data["surface_tank_stock"][j,:,:],
    )#[...,np.newaxis]


    # group 67
    #! renaming stRur to root_tank_stock
    #// data["stRur"][j:,:,:] = np.maximum(0, data["stRur"][j,:,:] - data["tr"][j,:,:])#[...,np.newaxis]
    data["root_tank_stock"][j:,:,:] = np.maximum(0, data["root_tank_stock"][j,:,:] - data["tr"][j,:,:])#[...,np.newaxis]

    # data["stRu"][j:,:,:] = np.maximum(0, data["stRu"][j,:,:] - data["tr"][j,:,:])
    # essais stTot
    # group 68
    #! renaming stTot to total_tank_stock
    #// data["stTot"][j:,:,:] = np.maximum(0, data["stTot"][j,:,:] - data["tr"][j,:,:])#[...,np.newaxis] 
    data["total_tank_stock"][j:,:,:] = np.maximum(0, data["total_tank_stock"][j,:,:] - data["tr"][j,:,:])#[...,np.newaxis] ## ok

    # group 69
    data["etr"][j:,:,:] = (data["tr"][j,:,:] + data["evap"][j,:,:]).copy()#[...,np.newaxis]
    
    # group 70
    data["etm"][j:,:,:] = (data["trPot"][j,:,:] + data["evapPot"][j,:,:]).copy()#[...,np.newaxis]

    return data