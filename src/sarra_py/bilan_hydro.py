import numpy as np
import xarray as xr
from sarra_py.bilan_carbo import estimate_kcp

def InitPlotMc(data, grid_width, grid_height, paramITK, paramTypeSol, duration):
    """
    Initializes variables related to crop residues boimass (mulch) in the data
    xarray dataset. This code has been adapted from the original InitPlotMc
    procedure, Bileau.pas code. Comments with tab indentation are from the
    original code. As the rain is the first variable to be initialized in the
    data xarray dataset, its dimensions are used to initialize the other
    variables.
    """


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
    #! renaminog stRuPrec with total_tank_stock_previous_value
    #// data["stRuPrec"] =  data["stTot"]
    data["total_tank_stock_previous_value"] =  data["total_tank_stock"]
    


    return data





def update_irrigation_tank_stock(j, data):
    """
    This function updates the water stock of the irrigation tank.
    
    If the simulation is run with automatic irrigation mode
    (`data["irrigAuto"]==True`), if the simulation is between phases 0 and 6,
    and if `root_tank_capacity` is lower than `surface_tank_capacity` (which
    indicates that the roots have not yet reached the limit between the surface
    compartment and deep compartment), `irrigation_tank_stock` will be set to
    the value of `surface_tank_stock`, which means, it will take the minimum
    value equal to `surface_tank_stock`. For phase 7, the existing
    `irrigation_tank_stock` value will be kept unchanged.

    Note : the logic of this function has not yet been validated in SARRA-Py, as
    simulations are mainly based on rainfed conditions.

    Args:
        j (int): Index of time step in data
        data (xarray Dataset): Dataset that contains various data fields

    Returns:
        xarray Dataset: updated data set with the irrigation_tank_stock field updated based on the conditions.
    """

    condition = (data["irrigAuto"][j, :, :] == True) & \
        (data["numPhase"][j, :, :] > 0) & \
        (data["numPhase"][j, :, :] < 6)

    data["irrigation_tank_stock"][j, :, :] = np.where(
        condition,
        xr.where(
            (data["root_tank_capacity"] < data["surface_tank_capacity"])[j, :, :],
            data["surface_tank_stock"][j, :, :],
            data["root_tank_stock"][j, :, :],
        ),
        data["irrigation_tank_stock"][j, :, :],
    )

    return data





def update_irrigation_tank_capacity(j, data):
    """
    This function updates the capacity if the irrigation tank.

    If the simulation is run with automatic irrigation mode
    (`data["irrigAuto"]==True`), if the current phase is between 0 and 6, and if
    the root tank capacity is less than the surface tank capacity (meaning that
    the roots have not reached the limit between the surface compartment and
    deep compartment), then `irrigation_tank_capacity` is set to the value of
    `surface_tank_capacity`, which is given a minimum value equal to the
    `surface_tank_capacity`. Otherwise, the irrigation tank capacity remains
    unchanged.

    Note : the logic of this function has not yet been validated in SARRA-Py, as
    simulations are mainly based on rainfed conditions.

    Args:
        j (int): Index of the time step being processed.
        data (xarray dataset): The input dataset containing all the information necessary to run the model.
    
    Returns:
        xarray dataset: The input dataset with updated values of the irrigation tank capacity.
    """

    condition = \
        (data["irrigAuto"][j, :, :] == True) & \
        (data["numPhase"][j, :, :] > 0) & \
        (data["numPhase"][j, :, :] < 6)

    data["irrigation_tank_capacity"][j, :, :] = np.where(
        condition,
        np.where(
            data["root_tank_capacity"][j,:,:] < data["surface_tank_capacity"],
            data["surface_tank_capacity"],
            data["root_tank_capacity"][j,:,:],
        ),
        data["irrigation_tank_capacity"][j, :, :],
    )

    return data





def compute_daily_irrigation(j, data, paramITK):
    """
    This function computes the total daily irrigation

    If the simulation is run with automatic irrigation mode
    (`data["irrigAuto"]==True`), if the current phase is between 0 and 6, and if
    the filling rate the irrigation tank is below the target filling value
    (`irrigAutoTarget`, decimal percentage), we first compute 90% of the
    difference between the current volume of water in the irrigation tank
    (`irrigation_tank_stock`) and the total capacity of the irrigation tank
    (`irrigation_tank_capacity`), bounded by a minimum of 0 and a maximum of
    `maxIrrig`. This computed value represents the amount of water to be added
    to the irrigation tank. If the above conditions are not met, the computed
    value is 0.

    Then, we calculate the total irrigation of the day by summing the estimated
    irrigation need (`irrigation`) with the previous irrigation history of the
    day (`irrigTotDay`).

    Note : the logic of this function has not yet been validated in SARRA-Py, as
    simulations are mainly based on rainfed conditions.

    Args:
        j: An integer representing the current day.
        data: A xarray dataset.
        paramITK: A dictionary of parameters.

    Returns:
        data: A xarray dataset with the updated irrigationTotDay field.
    """

    condition = (data["irrigAuto"][j, :, :] == True) & \
        (data["numPhase"][j, :, :] > 0) & \
        (data["numPhase"][j, :, :] < 6) & \
        (data["irrigation_tank_stock"][j, :, :] / data["irrigation_tank_capacity"][j,:,:] \
            < paramITK["irrigAutoTarget"])
        
    data["irrigTotDay"][j, :, :] = xr.where(
        condition,
        np.minimum(
            np.maximum(
                0,
                ((data["irrigation_tank_capacity"][j, :, :] - data["irrigation_tank_stock"][j, :, :]) * 0.9) \
                    - data["irrigation"][j, :, :]
                ),
            paramITK["maxIrrig"]
        ),
        0,
    )
    
    data["irrigTotDay"][j, :, :] = (
        data["irrigation"][j, :, :] + data["irrigTotDay"][j, :, :])

    return data



def compute_irrigation_state(j, data, paramITK):
    """
    This wrapper function computes the irrigation state for a given day,
    including the size and filling of the irrigation tank and the irrigation
    demand. It is computed only if `paramITK["irrigAuto"] == True` ; this means
    that irrigAuto shall be the same all over the grid, which is a reasonable
    assumption

    It has been Translated from the procedure EvalIrrigPhase, of the original
    Pascal codes bileau.pas and exmodules2.pas. Calculation precision is not
    taken into account anymore.

    irrigation_tank_stock and irrigation_tank_capacity are only computed in
    order to avoid issues with very shallow rooting, where calculation of
    filling of root_tank_capacity by root_tank_stock can be inappropriate and
    lead to inadapted results for automatic irrigation

    Notes from CB, 2014 : "Modification due à la prise en compte effet Mulch
    Soit on a une irrigation observée, soit on calcul la dose d'irrigation. Elle
    est calculée en fonction d'un seuil d'humidité (IrrigAutoTarget) et de
    possibilité technique ou choix (MaxIrrig, Precision). Dans cette gestion
    d'irrigation la pluie du jour n'est pas prise en compte."

    Args:
        j (int): Index of the day for which the irrigation state is being computed.
        data (xarray.Dataset): The input data, including the arrays for irrigation and correctedIrrigation.
        paramITK (dict): The parameters for the ITK model.

    Returns:
        xarray.Dataset: The updated data, including the computed values for the irrigation state.
    """

    if paramITK["irrigAuto"] == True :
        data = update_irrigation_tank_stock(j, data)
        data = update_irrigation_tank_capacity(j, data)
        data = compute_daily_irrigation(j, data, paramITK)

    return data





def compute_total_available_water(j, data):
    """
    This function computes the total available water for a day (mm) by adding
    rainfall and irrigation.

    This calculation is performed to allow for subsequent calculations of the
    mulch filling and water runoff.

    The available_water variable is later updated during the same day process
    list, so its value is not the same at the beginning and the end of the daily
    computation loop.

    This function has benn translated from the procedure PluieIrrig, of the
    original Pascal codes bileau.pas and exmodules2.pas.

    Args:
        j (int): The index of the current day.
        data (xarray.Dataset): The data set containing information about the rainfall, irrigation, and water availability.

    Returns:
        xarray.Dataset: The data set with updated information about the total water availability for the current day.
    """

    data["available_water"][j,:,:] = data["rain"][j,:,:] + data["irrigTotDay"][j,:,:]

    return data





def compute_water_captured_by_mulch(j, data, paramITK):
    """
    This function computes the height of water captured by the mulch.
    
    For this, we multiply the 'available_water' (rain + irrigation, in mm) by an
    exponential function taking both into consideration the mulch covering
    capacity (surfMc, ha/t) and mulch biomass (biomMc, kg/ha), representing the
    fraction of soil covered by mulch. If the fraction is 0 (no mulch), the
    value of water_captured_by_mulch is 0. 
    
    The value of water_captured_by_mulch is bounded by the maximum capacity of
    the mulch to gather water (humSatMc, kg H2O/kg biomass), minus stock of
    water already present in it (mulch_water_stock, mm).

    Note : the logic of this function has not yet been validated in SARRA-Py, as
    simulations are mainly based on situations without mulch.

    Notes from CB, 2014 :
    Hypotheses : A chaque pluie, on estime la quantité d'eau pour saturer le
    couvert. On la retire à l'eauDispo (pluie + irrig). On calcule la capacité
    maximum de stockage fonction de la biomasse et du taux de saturation
    rapportée en mm (humSatMc en kg H2O/kg de biomasse). La pluie est en mm : 1
    mm = 1 litre d'eau / m2 1 mm = 10 tonnes d'eau / hectare = 10 000 kg/ha La
    biomasse est en kg/ha pour se rapporter à la quantité de pluie captée en mm
    Kg H2O/kg Kg/ha et kg/m2 on divise par 10 000 (pour 3000 kg/ha à humSat 2.8
    kg H2O/kg on a un stockage max de 0.84 mm de pluie !?) Cette capacité à
    capter est fonction du taux de couverture du sol calculé comme le LTR SurfMc
    est spécifié en ha/t (0.39), on rapporte en ha/kg en divisant par 1000 On
    retire alors les mm d'eau captées à la pluie incidente. Le ruisselement est
    ensuite calculé avec l'effet de contrainte du mulch

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramITK (_type_): _description_

    Returns:
        _type_: _description_
    """

    data["water_captured_by_mulch"][j,:,:] = np.minimum(
        data["available_water"][j,:,:] * (1 - np.exp(-paramITK["surfMc"] / 1000 * data["biomMc"][j,:,:])),
        (paramITK["humSatMc"] * data["biomMc"][j,:,:] / 10000) - data["mulch_water_stock"][j,:,:],
    )

    return data


def update_available_water_after_mulch_filling(j, data):
    """
    This function updates available water after mulch filling.
    
    As some water is captured by the mulch (rain or irrigation water falling on
    it), the available_water is updated by subtracting the captured water
    (water_captured_by_mulch, mm) from the total available water
    (available_water, mm), to represent the remaining available water after
    capture by the mulch. This value is bounded by 0, as the available water
    cannot be negative.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    data["available_water"][j:,:,:] =  np.maximum(data["available_water"][j,:,:] - data["water_captured_by_mulch"][j,:,:], 0) 
    
    return data


def update_mulch_water_stock(j, data):
    """
    This function updates the water stock in mulch.

    The water stock in mulch is updated by adding the captured water (water_captured_by_mulch, mm)

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    data["mulch_water_stock"][j:,:,:] = (data["mulch_water_stock"][j,:,:] + data["water_captured_by_mulch"][j,:,:])
    
    return data



def fill_mulch(j, data, paramITK):

    """
    This wrapper function computes the filling of the mulch for a given day.

    It has been translated from the procedure PluieIrrig, of the original Pascal codes
    bileau.pas and exmodules2.pas

    For more details, it is advised to refer to the works of Eric Scopel (UR
    AIDA), and the PhD dissertation of Fernando Maceina. 
    """

    data = compute_water_captured_by_mulch(j, data, paramITK)
    data = update_available_water_after_mulch_filling(j, data)
    data = update_mulch_water_stock(j, data)

    return data


def estimate_runoff(j, data):
    """
    This function evaluates the water runoff (mm).
    
    If the quantity of rain (mm) is above the runoff_threshold (mm), runoff is computed as the difference between the available water
    (mm) and the runoff_threshold  multiplied by
    the runoff_rate (%). Else, runoff value is set to 0.

    runoff_threshold and runoff_rate are defined in load_iSDA_soil_data
    
    Question : should runoff be computed taking in consideration water captured by
    mulch to account for mulch effect on runoff mitigation ?

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    
    # group 11
    data["runoff"][j,:,:] = xr.where(
        data["rain"][j,:,:] > data["runoff_threshold"],
        (data["available_water"][j,:,:]  - data["runoff_threshold"]) * data["runoff_rate"],
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
    data["available_water"][j:,:,:] = (data["available_water"][j,:,:] - data["runoff"][j,:,:])
    return data




def compute_runoff(j, data):
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




def initialize_root_tank_capacity(j, data, paramITK):
    """
    updating stRurMax/root_tank_capacity, step 1 :
    
    stRurMax, also called ruRac in some versions of the model, is the root_tank_capacity.

    At the phase change between phases 0 and 1 (initialisation), the maximum
    root water storage is initialised by multiplying the initial root depth
    (profRacIni, mm) with the soil water storage capacity (ru, mm/m). This
    value is broadcasted on the time series. For every other day in the cycle,
    the value remains unchanged.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramITK (_type_): _description_

    Returns:
        _type_: _description_
    """
    # group 14
    #! renaming stRurMax to root_tank_capacity
    #// data["stRurMax"][j:,:,:] = np.where(
    data["root_tank_capacity"][j:,:,:] = xr.where(
        (data["changePhase"][j,:,:] == 1) & (data["numPhase"][j,:,:] == 1),
        paramITK["profRacIni"] / 1000 * data["ru"],
        #// data["stRurMax"][j,:,:],
        data["root_tank_capacity"][j,:,:],
    )

    return data



def estimate_delta_root_tank_capacity(j, data):
    """
    Updates daily root capacity variation (delta_root_tank_capacity, in mm
    water/day) based on the current phase of the plant, the daily root growth
    speed, and the drought stress coefficient.

    The daily root capacity variation is calculated as the product of soil water
    storage capacity (ru), the daily root growth speed (vRac), and a coefficient
    (cstr + 0.3). This coefficient is capped at 1.0.

    The daily root capacity variation is modulated by drought stress only when the
    root tank capacity is greater than the surface tank capacity and the current
    phase is strictly greater than 1 and at the day of phase change. If the root
    tank capacity is lower than the surface tank capacity or if the current phase is
    1 or below or not at the day of phase change, the daily root capacity variation
    remains unchanged. 

    The drought stress coefficient, cstr, measures the level of drought stress with
    0 being full stress. The root growth speed is assumed to still occur during a
    drought stress as a matter of survival, with a certain level of tolerance given
    by the [0.3, 1] bound of the coefficient.

    

    
    Updating delta_root_tank_capacity / dayVrac (daily variation in water height
    accessible to roots, mm water/day) :
    
    At the day of phase change, for phases strictly above 1, and for which
    root_tank_capacity is greater than surface_tank_capacity, the variation of
    root tank capacity delta_root_tank_capacity is computed as the product of
    soil water storage capacity (ru, mm/m), the daily root growth speed (vRac,
    mm/day), and a coefficient, the latter being equal to the drought stress
    coefficient (cstr) plus 0.3, with a maximum bound of 1.0. 
    
    That is to say, when the root_tank_capacity is greater than
    surface_tank_capacity, the root growth speed is modulated by drought stress.
    When root_tank_capacity is lower than surface_tank_capacity, the root growth
    speed is not modulated by drought stress.
    
    When we are not at the day of phase change, or if we are at phase of 1 and
    below, delta_root_change_capacity is unchanged.
    
    cstr is the drought stress coefficient, with a value of 0 meaning full stress.

    Why is delta_root_tank_capacity bounded in [0.3, 1] ? According to Chriatian
    BARON, this is based on the hypothesis that during a drought stress (cstr =
    0), the plant will still grow roots as a matter of survival. Furthermore,
    using the [0.3, 1] bound is a way to tell that in the [0.7, 1] cstr
    interval, there is no effect of drought stress on the root growth speed,
    allowing for a certain level of tolerance of the plant. 
    
    Args:
        j (int): The current iteration step of the process.
        data (xarray.Dataset): The input data containing relevant information.

    Returns:
        xarray.Dataset: The updated input data with the daily root capacity variation calculated and stored.
    """

    # group 15  
    # ! simplified conditions
    # // condition = (data["numPhase"][j,:,:] > 0) & \
    # //       np.invert((data["numPhase"][j,:,:] == 1) & (data["changePhase"][j,:,:] == 1))
    condition = (data["numPhase"][j,:,:] > 1) & (data["changePhase"][j,:,:] == 1)
    #! renaming dayVrac to delta_root_tank_capacity
    #// data["dayVrac"][j,:,:] = np.where(
    data["delta_root_tank_capacity"][j,:,:] = xr.where(
        condition,
        xr.where(
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

    return data




def update_delta_root_tank_capacity(j, data):
    """
    updating delta_root_tank_capacity : 
    
    At the day of phase change, for phases strictly above 1, and for which the
    difference between the water height to humectation front (hum, mm) and the
    root_tank_capacity is less than the delta_root_tank_capacity,
    delta_root_tank_capacity is updated to be equal to the difference between
    the water height to humectation front and the root_tank_capacity. In other
    words, the change in root tank capacity delta_root_tank_capacity is limited
    by the water height to humectation front.
    
    For any other day or if root_tank_capacity is above
    delta_root_tank_capacity, delta_root_tank_capacity value is unchanged.

    Args:
        j (_type_): _description_
        data (_type_): _description_
    """

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

    return data




def update_root_tank_capacity(j, data):
    """
    updating root_tank_capacity/stRurMax/ruRac, step 2 :
    
    At the day of phase change, for phases strictly above 1, root_tank_capacity
    is updated to be summed with the change in root water storage capacity delta_root_tank_capacity.
    In other words, root_tank_capacity is incremented by the change in root water
    storage capacity linked to root growth.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

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

    return data




def update_root_tank_stock(j, data):
    """
    updating root_tank_stock/stRur/stockrac :
    
    At the day of phase change, for phases strictly above 1, and for which
    the root_tank_capacity is above surface_tank_capacity (meaning that
    roots go beyond the surface water storage capacity), root_tank_stock
     is incremented by delta_root_tank_capacity.
    
    However, if root_tank_capacity is BELOW surface_tank_capacity (meaning
    that roots do not plunge into the deep reservoir), root_tank_stock is
    updated to be equal to surface_tank_stock minus 1/10th of the
    surface_tank_capacity, multiplied by the ratio between
    root_tank_capacity and surface_tank_capacity. That is to say "we take at
    the prorata of depth and surface stock".
    
    For any other day, root_tank_stock is unchanged.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    # group 18
    # ! simplified conditions
    # // condition = (data["numPhase"][j,:,:] > 0) & np.invert((data["changePhase"][j,:,:] == 1) & (data["numPhase"][j,:,:] == 1)),
    condition = (data["numPhase"][j,:,:] > 1) & (data["changePhase"][j,:,:] == 1),
    
    #! renaming stRur to root_tank_stock
    #// data["stRur"][j:,:,:] = np.where(
    data["root_tank_stock"][j:,:,:] = xr.where(
        condition,
        xr.where(
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
        ).expand_dims("time", axis=0), 
        #! renaming stRur to root_tank_stock
        #// data["stRur"][j,:,:],
        data["root_tank_stock"][j,:,:],
    )

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

    data = initialize_root_tank_capacity(j, data, paramITK)
    data = estimate_delta_root_tank_capacity(j, data)
    data = update_delta_root_tank_capacity(j, data)
    data = update_root_tank_capacity(j, data)
    data = update_root_tank_stock(j, data)

    return data




####################### list of functions for rempliRes #######################





def condition_end_of_cycle(j,data):
    """
    Returns conditions needed to apply functions related to end of cycle.

    Returns:
        _type_: _description_
    """
    condition = (data["numPhase"][j,:,:] == 7) & (data["changePhase"][j,:,:] == 1)
    return condition





def update_humPrec_for_end_of_cycle(j, data):
    """
    This function saves information about the humectation front depth at the end
    of a growth cycle so it can be used in the next cycle.

    humPrec is initialized in the function InitPlotMc, and set to be equal to
    hum, itself being initialized to take the maximum value between
    surface_tank_capacity, root_tank_capacity and total_tank_stock.

    At the harvest date (numPhase = 7), the humPrec variable is set to equal the
    highest value between hum (mm, humectation front depth) and
    surface_tank_capacity (mm). This value is broadcasted over the time
    dimension.

    At any other point in time, its value is unchanged.

    This means...

    Args:
        j (int): number of the day
        data (xarray dataset): _description_
    Returns:
        xarray dataset: _description_
    """
    # group 20
    condition = condition_end_of_cycle(j,data)

    data["humPrec"][j:,:,:] = np.where(
        condition,
        #! renaming ruSurf to surface_tank_capacity
        #// np.maximum(data["hum"][j,:,:], data["ruSurf"][j,:,:]),
        np.maximum(data["hum"][j,:,:], data["surface_tank_capacity"]),
        data["humPrec"][j,:,:],
    )

    return data





def update_hum_for_end_of_cycle(j, data):
    """
    This function updates information about the humectation front depth at the end
    of a growth cycle.

    At the harvest date (numPhase = 7), the hum variable is set to equal the
    surface_tank_capacity (mm). This value is broadcasted over the time
    dimension.

    At any other point in time, its value is unchanged.

    This means...

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    # group 21
    condition = condition_end_of_cycle(j,data)

    data["hum"][j:,:,:] = np.where(
        condition,
        #! renaming ruSurf to surface_tank_capacity
        #// data["ruSurf"][j,:,:],
        data["surface_tank_capacity"],
        data["hum"][j,:,:],
    )

    return data





def update_stRurMaxPrec_for_end_of_cycle(j, data):
    """
    When the phase changes from 7 to 1, the stRurMaxPrec (mm, previous
    maximum water capacity to root front) is set to equal root_tank_capacity
    (mm). Value is broadcasted along time dimension.
    For every other day, it keeps its initial value of 0. 
    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    # group 22
    condition = condition_end_of_cycle(j,data)
    #! renaming stRurMaxPrec to root_tank_capacity_previous_season
    #// data["stRurMaxPrec"][j:,:,:] = np.where(
    data["root_tank_capacity_previous_season"][j:,:,:] = np.where(    
        condition,
        #! renaming stRurMax to root_tank_capacity
        #// data["stRurMax"][j,:,:],
        data["root_tank_capacity"][j,:,:],
        #! renaming stRurMaxPrec to root_tank_capacity_previous_season
        #// data["stRurMaxPrec"][j,:,:],
        data["root_tank_capacity_previous_season"][j,:,:],
    )
    return data





def update_stRurPrec_for_end_of_cycle(j, data):
    """
    when the phase changes from 7 to 1, stRurPrec is set to equal
    stRur/stRurMax, that is to say the ratio of the water storage capacity of
    the root reservoir. Otherwise, it stays at its initial value of 0. Its value
    is broadcasted along j.

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """

    # group 23
    condition = condition_end_of_cycle(j,data)
    data["stRurPrec"][j:,:,:] = np.where(
        condition,
        #! renaming stRur to root_tank_stock
        #! renaming stRurMax to root_tank_capacity
        #// data["stRur"][j,:,:]/data["stRurMax"][j,:,:],
        data["root_tank_stock"][j,:,:]/data["root_tank_capacity"][j,:,:],
        data["stRurPrec"][j,:,:],
    )
    return data





def update_stRuPrec_for_end_of_cycle(j, data):
    """
    when the phase changes from 7 to 1, the stRuPrec (mm, previous water
    storage capacity of the global reservoir) is set to equal the differe,ce
    between stTot (mm, total water storage capacity of the global reservoir)
    and stRurSurf (mm, water storage capacity of the surface reservoir)

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    # group 24
    #! stRurSurf is not defined... we may want to drop this group
    condition = condition_end_of_cycle(j,data)

    #! renaming stRuPrec to total_tank_stock_previous_value
    #// data["stRuPrec"][j:,:,:] = np.where(
    data["total_tank_stock_previous_value"][j:,:,:] = np.where(
        condition,
        #! renaming stTot to total_tank_stock
        #! renaming stRuSurf with surface_tank_stock
        #// data["stRu"][j,:,:] - data["stRurSurf"][j,:,:],
        data["total_tank_stock"][j,:,:] - data["surface_tank_stock"][j,:,:], # essai stTot
        #! renaming stRuPrec to total_tank_stock_previous_value
        #// data["stRuPrec"][j,:,:],
        data["total_tank_stock_previous_value"][j,:,:],
    )

    return data





def reset_total_tank_capacity(j, data):
    """
    This function resets the value total_tank_capacity/stRuMax at each loop.
    
    ? Why redfining stRuMax at each loop ? Neither ru, profRu 
    ? nor total_tank_capacity are modified during the simulation.

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    
    # group 25
    #! renaming stRuMax to total_tank_capacity
    #// data["stRuMax"][j:,:,:] = (data["ru"] * data["profRu"] / 1000) #.copy()#[...,np.newaxis]
    data["total_tank_capacity"][j:,:,:] = (data["ru"] * data["profRu"] / 1000)
    return data





def update_surface_tank_stock(j, data):
    """
    This function updates the value of surface_tank_stock.
    
    We update surface_tank_stock by adding the eauDispo, which as this point is
    the water available from 1) rain, 2) irrigation for the day after estimation
    of intake by mulch, and 3) runoff. However, we do not allow
    surface_tank_stock to exceed 110% of the surface_tank_capacity.

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    # group 27
    #! renaming stRuSurf to surface_tank_stock
    #// data["stRuSurf"][j:,:,:] = np.minimum(
    data["surface_tank_stock"][j:,:,:] = np.minimum(
        #// data["stRuSurf"][j,:,:] + data["eauDispo"][j,:,:],
        data["surface_tank_stock"][j,:,:] + data["available_water"][j,:,:],
        #! renaming ruSurf to surface_tank_capacity
        #// 1.1 * data["ruSurf"][j,:,:]
        1.1 * data["surface_tank_capacity"]
    )
    return data





def estimate_transpirable_water(j, data):
    """
    This function estimates the daily volume of transpirable water.
    
    eauTranspi (mm, water transpirable) is the water available for
    transpiration from the surface reservoir.

    If surface_tank_stock at the end of the previous day (index j-1) is
    lower than 10% of the surface_tank_capacity, the water available for
    transpirable water equals the water available for the day (eauDispo),
    minus the difference between 1/10th of the surface_tank_capacity and
    surface_tank_stock. This transpirable water has a min bound at 0 mm.
    
    Said otherwise, a part of the water available for the day (eauDispo) is
    considered as bound to the surface reservoir and cannot be transpired. 
    
    If surface_tank_stock at the end of the previous day (index j-1) is
    upper than 10% of the surface_tank_capacity, transpirable water equals
    eauDispo.

    Remark : if the use of j-1 indices is too problematic, it seems feasible to
    run this function just before update_surface_tank_stock.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    # group 28
    data["eauTranspi"][j,:,:] = np.where(
        # ! modifying to replace stRuSurfPrec by stRuSurf at undex j-1
        #! renaming ruSurf to surface_tank_capacity
        #! renaming stRuSurfPrec to surface_tank_stock
        # // data["stRuSurfPrec"][j,:,:] < data["ruSurf"][j,:,:]/10,
        data["surface_tank_stock"][j-1,:,:] < 0.1 * data["surface_tank_capacity"],
        np.maximum(
            0,
            # ! modifying to replace stRuSurfPrec by stRuSurf at iundex j-1
            #! renaming ruSurf to surface_tank_capacity
            #! renaming stRuSurf to surface_tank_stock
            # //data["eauDispo"][j,:,:] - (data["ruSurf"][j,:,:]/10 - data["stRuSurfPrec"][j,:,:])
            data["available_water"][j,:,:] - (0.1 * data["surface_tank_capacity"] - data["surface_tank_stock"][j-1,:,:])
            ),
        data["available_water"][j,:,:],
    )

    return data





def update_total_tank_stock(j, data):
    """
    This functions updates the value of total_tank_stock with the value of
    transpirable water.
    
    ? why incrementing stTot by eauTranspi ?
    ? we then consider that transpirable water is the water that fills the total_tank_stock ?

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    # group 29
    #! renaming stTot with total_tank_stock
    #// data["stTot"][j:,:,:] = (data["stTot"][j,:,:] + data["eauTranspi"][j,:,:]).copy()#[...,np.newaxis]
    data["total_tank_stock"][j:,:,:] = (data["total_tank_stock"][j,:,:] + data["eauTranspi"][j,:,:])

    return data





def update_delta_total_tank_stock(j, data):
    """
    This function estimates delta_total_tank_stock

    delta_total_tank_stock is the positive variation of transpirable water
    stock. It is computed as the difference between the total_tank_stock and
    stRuPrec, bound in 0. Thus, it can only have a positive value. stRuPrec is
    initialized to be equal to total_tank_stock at the beginning of the
    simulation. total_tank_stock is initialized with stockIrr parameter. Thus,
    simulations should start with a 0 value.

    stRuPrec is updated at each cycle with the update_struprec function.

    
    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    # group 30
    #! we propose a different version based on stTot
    #! renaming stTot to total_tank_stock
    #! renaming stRuVar to delta_total_tank_stock
    #! renaming stRuPrec to total_tank_stock_previous_value
    #// data["stRuVar"][j:,:,:] = np.maximum(0, data["stTot"][j,:,:] - data["stRuPrec"][j,:,:])[...,np.newaxis]
    data["delta_total_tank_stock"][j:,:,:] = np.maximum(0, data["total_tank_stock"][j,:,:] - data["total_tank_stock_previous_value"][j,:,:])
    return data





def conditions_rempliRes(j,data):
    """_summary_
    Returns:
        _type_: _description_
    """

    #! renaming stRuVar with delta_total_tank_stock
    #//condition_1 = (data["stRuVar"][j,:,:] > data["hum"][j,:,:])
    condition_1 = (data["delta_total_tank_stock"][j,:,:] > data["hum"][j,:,:])

    #! renaming stRurMaxPrec to root_tank_capacity_previous_season
    #// condition_2 = (data["hum"][j,:,:] <= data["stRurMaxPrec"][j,:,:])
    condition_2 = (data["hum"][j,:,:] <= data["root_tank_capacity_previous_season"][j,:,:])

    #! we replace humPrec by hum with indice j-1
    #// condition_3 = (data["hum"][j,:,:] < data["humPrec"][j,:,:])
    condition_3 = (data["hum"][j,:,:] < data["humPrec"][j,:,:])

    return condition_1, condition_2, condition_3





def update_total_tank_stock_step_2(j, data):
    """
    This function performs the second update of total_tank_stock/stTot/stRu in the
    reservoir filling wrapper function. It will increase the total_tank_stock
    depending on the variation of transpirable water and height of humectation
    front.

    test image markdown
    ![Drag Racing](Dragster.jpg)

    In this function, if the variation of transpirable water
    (delta_total_tank_stock) increases above the depth of humectation front
    (hum), if the depth of humectation front (hum) is above the
    root_tank_capacity_previous_season (condition 1 passed, and 2 failed, which
    should be the case for most of the simulations that will be single-season),
    and if the depth of humectation front (hum) has decreased since the previous
    day, then total_tank_stock takes delta_total_tank_stock as value. If the
    depth of humectation front did not change or increased since the previous
    day (humPrec), then total_tank_stock is unchanged.

    Notably, root_tank_capacity_previous_season is initialized at 0, and takes
    another value only at end of cycle ; hum is initialized at a value different
    from 0 and evolves daily between delta_total_tank_stock and
    total_tank_capacity.

    humPrec is initialized with the same value as hum. However, in the
    update_humPrec_for_end_of_cycle function, at the day of transition between
    phase 7 and phase 0, it takes hum as value, with a minimum bound of
    surface_tank_capacity.

    Starting from second simulation season (root_tank_capacity_previous_season
    != 0), if the variation of transpirable water (delta_total_tank_stock)
    increases above the depth of humectation front (hum), and if the depth of
    humectation front stays below or equel to the total soil capacity
    (conditions 1 and 2 passed), then we increase the value of total_tank_stock
    by a the difference of water height between the variation of total tank
    stock (delta_total_tank_stock) and the depth of humectation front (hum),
    proportionally to the filling of the root tank capacity of previous season
    (stRurPrec). Thus, if the root tank is empty, total_tank_stock will remain
    unchanged, and if the root tank is full, total_tank_stock will be increased
    up to the amount of water making the difference between quantity of water
    for humectation front and the variation in daily transpirable water.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    condition_1, condition_2, condition_3 = conditions_rempliRes(j,data)

    #! renaming stTot to total_tank_stock
    #// data["stTot"][j:,:,:] = np.where(
    data["total_tank_stock"][j:,:,:] = np.where(
        condition_1,
        np.where(
            #! 
            condition_2, 
            #! we replace stRurPrec with stRur at indice j-1
            #! renaming stRur to root_tank_stock
            #! renaming stTot to total_tank_stock
            #! renaming stRuVar with delta_total_tank_stock
            #// data["stTot"][j,:,:] + (data["stRuVar"][j,:,:] - data["hum"][j,:,:]) * data["stRurPrec"][j,:,:],
            data["total_tank_stock"][j,:,:] + (data["delta_total_tank_stock"][j,:,:] - data["hum"][j,:,:]) * data["stRurPrec"][j,:,:],
            np.where(
                condition_3,
                #! renaming stRuVar with delta_total_tank_stock
                #//data["stRuVar"][j,:,:],
                data["delta_total_tank_stock"][j,:,:],
                #! renaming stTot to total_tank_stock
                #// data["stTot"][j,:,:],
                data["total_tank_stock"][j,:,:],
            ),
        ),
        #! renaming stTot to total_tank_stock  
        #// data["stTot"][j,:,:],
        data["total_tank_stock"][j,:,:],
    )

    return data






def update_stRuPrec(j, data):
    """
    This function performs the update of
    total_tank_stock_previous_value/stRuPrec in the reservoir filling wrapper
    function. It will decrease the total_tank_stock_previous_value depending on
    the variation of transpirable water and height of humectation front.

    test image markdown ![Drag Racing](Dragster.jpg)

    In this function, if the variation of transpirable water
    (delta_total_tank_stock) increases above the depth of humectation front
    (hum), if the depth of humectation front (hum) is above the
    root_tank_capacity_previous_season (condition 1 passed, and 2 failed, which
    should be the case for most of the simulations that will be single-season),
    and if the depth of humectation front (hum) has decreased since the previous
    day (condition 3 passed), then total_tank_stock_previous_value equals 0. If
    the depth of humectation front did not change or increased since the
    previous day (humPrec), then total_tank_stock_previous_value is unchanged.

    Notably, root_tank_capacity_previous_season is initialized at 0, and takes
    another value only at end of cycle ; hum is initialized at a value different
    from 0 and evolves daily between delta_total_tank_stock and
    total_tank_capacity.

    humPrec is initialized with the same value as hum. However, in the
    update_humPrec_for_end_of_cycle function, at the day of transition between
    phase 7 and phase 0, it takes hum as value, with a minimum bound of
    surface_tank_capacity.

    Starting from second simulation season (root_tank_capacity_previous_season
    != 0), if the variation of transpirable water (delta_total_tank_stock)
    increases above the depth of humectation front (hum), and if the depth of
    humectation front stays below or equel to the total soil capacity
    (conditions 1 and 2 passed), then we decrease the value of
    total_tank_stock_previous_value by a the difference of water height between
    the variation of total tank stock (delta_total_tank_stock) and the depth of
    humectation front (hum), proportionally to the filling of the root tank
    capacity of previous season (stRurPrec). Thus, if the root tank is empty,
    total_tank_stock_previous_value will remain unchanged, and if the root tank
    is full, total_tank_stock_previous_value will be decreased up to the amount
    of water making the difference between quantity of water for humectation
    front and the variation in daily transpirable water.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    condition_1, condition_2, condition_3 = conditions_rempliRes(j,data)

    # group 32
    #! renaming stRuPrec with total_tank_stock_previous_value
    #// data["stRuPrec"][j:,:,:] = np.where(
    data["total_tank_stock_previous_value"][j:,:,:] = np.where(
        condition_1,
        np.where(
            condition_2,
            #! replacing stRurPrec with ratio formula
            #! renaming stRuVar with delta_total_tank_stock
            #! renaming stRuPrec with total_tank_stock_previous_value
            #//np.maximum(0, data["stRuPrec"][j,:,:] - (data["stRuVar"][j,:,:] - data["hum"][j,:,:]) * data["stRurPrec"][j,:,:]),
            np.maximum(0, data["total_tank_stock_previous_value"][j,:,:] - (data["delta_total_tank_stock"][j,:,:] - data["hum"][j,:,:]) * data["stRurPrec"][j,:,:]),
            np.where(
                condition_3,
                0,
                #! renaming stRuPrec with total_tank_stock_previous_value
                #// data["stRuPrec"][j,:,:],
                data["total_tank_stock_previous_value"][j,:,:],
            ),
        ),
        #! renaming stRuPrec with total_tank_stock_previous_value
        #// data["stRuPrec"][j,:,:],
        data["total_tank_stock_previous_value"][j,:,:],
    )

    return data





def update_delta_total_tank_stock_step_2(j, data):
    """



    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    condition_1, condition_2, condition_3 = conditions_rempliRes(j,data)

    # groupe 33
    #! renaming stRuVar with delta_total_tank_stock
    #// data["stRuVar"][j:,:,:] = np.where(
    data["delta_total_tank_stock"][j:,:,:] = np.where(
        condition_1,
        np.where(
            condition_2,
            #! renaming stRuVar with delta_total_tank_stock
            #// data["stRuVar"][j,:,:] + (data["stRuVar"][j,:,:] - data["hum"][j,:,:]) * data["stRurPrec"][j,:,:],
            data["delta_total_tank_stock"][j,:,:] + (data["delta_total_tank_stock"][j,:,:] - data["hum"][j,:,:]) * data["stRurPrec"][j,:,:],
            np.where(
                condition_3,
                #! renaming stRuVar with delta_total_tank_stock
                #! renaming stRuPrec with total_tank_stock_previous_value
                #// data["stRuVar"][j,:,:] + data["stRuPrec"][j,:,:],
                data["delta_total_tank_stock"][j,:,:] + data["total_tank_stock_previous_value"][j,:,:],
                #! renaming stRuVar with delta_total_tank_stock
                #// data["stRuVar"][j,:,:],
                data["delta_total_tank_stock"][j,:,:],   
            ),
        ),
        #! renaming stRuVar with delta_total_tank_stock
        #// data["stRuVar"][j,:,:],
        data["delta_total_tank_stock"][j,:,:],
    )

    return data





def update_hum(j, data):
    """
    This function updates the depth to humectation front (hum) to be the maximum
    value between the depth to humectation front (hum) and
    delta_total_tank_stock (that is to say depth of humectation front can only
    increase), bounded by total_tank_capacity (that is to say humectation front
    can not go deep indefinitely).

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    # groupe 34
    #! renaming stRuVar with delta_total_tank_stock
    #// data["hum"][j:,:,:] = np.maximum(data["stRuVar"][j,:,:], data["hum"][j,:,:])#[...,np.newaxis]
    data["hum"][j:,:,:] = np.maximum(data["delta_total_tank_stock"][j,:,:], data["hum"][j,:,:])

    # groupe 35
    #! renaming stRuMax to total_tank_capacity
    #// data["hum"][j:,:,:] = np.minimum(data["stRuMax"][j,:,:], data["hum"][j,:,:])#[...,np.newaxis]
    data["hum"][j:,:,:] = np.minimum(data["total_tank_capacity"][j,:,:], data["hum"][j,:,:])
    return data





def condition_total_tank_overflow(j,data):
    """_summary_

    Returns:
        _type_: _description_
    """
    condition = (data["total_tank_stock"][j,:,:] > data["total_tank_capacity"][j,:,:])
    return condition





def update_dr(j, data):
    """
    This function estimates the daily drainage (dr). When total tank overflows, it
    computes drainage from the differences between the total_tank_stock (that is
    to say the total and total_tank_capacity.

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    #! renaming stTot to total_tank_stock
    #! renaming stRuMax to total_tank_capacity
    #// condition = (data["stTot"][j,:,:] > data["stRuMax"][j,:,:])
    condition = condition_total_tank_overflow(j,data)
    # groupe 36
    # essais stTot
    data["dr"][j,:,:] = np.where(
        condition,
        #! renaming stTot to total_tank_stock
        #! renaming stRuMax to total_tank_capacity
        #// data["stRu"][j,:,:] - data["stRuMax"][j,:,:],
        data["total_tank_stock"][j,:,:] - data["total_tank_capacity"][j,:,:],
        0,
    )
    return data





def update_total_tank_stock_step_3(j, data):
    """
    This function updates the total tank stock where these is overflow occuring.
    When capacity of total tank is exceeded, it corrects the stock value with
    maximum capacity of total tank.

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """

    #! renaming stTot to total_tank_stock
    #! renaming stRuMax to total_tank_capacity
    #// condition = (data["stTot"][j,:,:] > data["stRuMax"][j,:,:])
    condition = condition_total_tank_overflow(j,data)
    # groupe 37
    # essais stTot
    #! renaming stTot to total_tank_stock
    #! renaming stRuMax to total_tank_capacity
    #// data["stRu"][j,:,:] = np.where(
    #// data["stTot"][j:,:,:] = np.where(   
    data["total_tank_stock"][j:,:,:] = np.where(  
        condition,
        #// data["stRuMax"][j,:,:],
        data["total_tank_capacity"][j,:,:],
        # data["stRu"][j,:,:],
        #// data["stTot"][j,:,:],
        data["total_tank_stock"][j,:,:],
    )#[...,np.newaxis]
    return data





def update_hum_step_2(j, data):
    """
    We update the depth to humectation front (hum) again, to reflect eventual changes in
    total_tank_stock values.

    ? we could have placed the previous hum update function here

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    # groupe 38
    # // avant modif 10/06/2015
    # data["hum"][j:,:,:] = np.maximum(data["hum"][j,:,:], data["stRu"][j,:,:])
    # essais stTot
    #! renaming stTot to total_tank_stock
    #// data["hum"][j:,:,:] = np.maximum(data["hum"][j,:,:], data["stTot"][j,:,:])[...,np.newaxis]
    data["hum"][j:,:,:] = np.maximum(data["hum"][j,:,:], data["total_tank_stock"][j,:,:])#[...,np.newaxis]
    #! en conflit avec le calcul précédent de hum

    return data





def update_root_tank_stock_step_2(j, data):
    """

    Finally, we update root tank stock (root_tank_stock) with the computed
    values First we increment root_tank_stock with transpirable water
    (eauTranspi), within the limits of root_tank_capacity. Then, we limit the
    value of root_tank_stock within total_tank_stock

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
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





def rempliRes(j, data):


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

    # section 1 : updating the end_of_cycle memory variables

    # in order to save resources, we test if there is at least one pixel at phase 7
    # and one pixel at changePhase 1 in the current time step before applying the "end_of_cycle" functions

    # if (np.any(data["numPhase"][j,:,:] == 7)) & (np.any(data["changePhase"][j,:,:] == 1)):
        
    data = update_humPrec_for_end_of_cycle(j, data)
    data = update_hum_for_end_of_cycle(j, data)
    data = update_stRurMaxPrec_for_end_of_cycle(j, data)
    data = update_stRurPrec_for_end_of_cycle(j, data)
    data = update_stRuPrec_for_end_of_cycle(j, data)
    

    data = reset_total_tank_capacity(j, data) # verif ok
    
    # # filling the surface tank with available water
    data = update_surface_tank_stock(j, data) # verif ok

    # # estimates transpirable water
    data = estimate_transpirable_water(j, data) # verif ok

    # # increments total tank stock with transpirable water 
    # # (meaning that total tank stock may represent a transpirable water tank)
    data = update_total_tank_stock(j, data) # verif ok





    # # estimating positive delta between total_root_tank and stRuPrec
    data = update_delta_total_tank_stock(j, data) # verif ok


    
    # # first we update total_tank_stock that can 1) take delta_total_tank_stock or 2) be unchanged
    data = update_total_tank_stock_step_2(j, data)# verif ok
    # # then total_tank_stock_previous_value can 1) take 0 or 2) be unchanged
    data = update_stRuPrec(j, data) #????
    # # delta_total_tank_stock can 1) be incremented of total_tank_stock_previous_value or 2) be unchanged
    data = update_delta_total_tank_stock_step_2(j, data)
    
    # # # here, in case 1, In this function, if the variation of transpirable water
    # # (delta_total_tank_stock) increases above the depth of humectation front
    # # (hum), if the depth of humectation front (hum) is above the
    # # root_tank_capacity_previous_season (condition 1 passed, and 2 failed,
    # # which should be the case for most of the simulations that will be
    # # single-season), and if the depth of humectation front (hum) has decreased
    # # since the previous day (condition 3 passed), then total_tank_stock takes the value of 
    # # delta_total_tank_stock, total_tank_stock_previous_value equals 0, and 
    # # delta_total_tank_stock is incremented by total_tank_stock_previous_value.
    # # 
    # # in case 2, nothing happens.


    # # update_hum manages increase in hum 
    data = update_hum(j, data)

    # # in case of overflowing...
    # # calculating drainage
    data = update_dr(j, data)
    # # limiting the total_tank_stock to the total_tank_capacity (when overflowing)
    data = update_total_tank_stock_step_3(j, data)

    # # update again hum value, but we could merge functions with update_hum
    data = update_hum_step_2(j, data)

    # # filling root_tank_stock with transpirable water, within the limits of total_tank_stock
    data = update_root_tank_stock_step_2(j, data)        

    return data


########################################################################################





def estimate_fesw(j, data):
    """
    This function estimates the fraction of evaporable soil water (fesw, mm).
    fesw is defined as the ratio of water stock in the surface tank over 110% of
    the surface tank capacity.
    
    It is adapted from the EvalFESW procedure, from bileau.pas and
    bhytypeFAO.pas files from the original FORTRAN code.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    #! renaming stRuSurf to surface_tank_stock
    #! renaming ruSurf with surface_tank_capacity
    #// data["fesw"][j,:,:] = data["stRuSurf"][j,:,:] / (data["ruSurf"][j,:,:] + data["ruSurf"][j,:,:] / 10)
    data["fesw"][j,:,:] = data["surface_tank_stock"][j,:,:] / (data["surface_tank_capacity"] + 0.1 * data["surface_tank_capacity"])

    return data





def estimate_kce(j, data, paramITK):
    """
    This function estimates the coefficient of evaporation from the soil (kce).

    This approach takes into consideration three factors acting on limitation of
    kce :

    1) ltr : plant cover, 1 = no plant cover, 0 = full plant cover
    2) Mulch - permanent covering effect : we consider a value of 1.0 for no
    covering, and 0.0 is full covering with plastic sheet ; this mulch parameter
    has been used in previous versions of the model where evolution of mulch
    biomass was not explicitely taken into consideration, can be used in the
    case of crops with self-mulching phenomena, where a standard mulch parameter
    value of 0.7 can be applied.
    3) Mulch - evolutive covering effect BiomMc : biomass of mulch  

    This function has been adapted from EvalKceMC procedure, bileau.pas and
    exmodules 2.pas from the original FORTRAN code. In its spirit, it looks like
    it has been adapted from the dual crop coefficient from the FAO56 paper. But
    this is still to confirm on a point of view of the history of the model.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramITK (_type_): _description_

    Returns:
        _type_: _description_
    """

    data["kce"][j,:,:] = data["ltr"][j,:,:] * paramITK["mulch"] * \
        np.exp(-paramITK["coefMc"] * paramITK["surfMc"] * data["biomMc"][j,:,:]/1000)
    
    return data





def estimate_soil_potential_evaporation(j, data):
    """
    This function computes estimation of potential soil evaporation (mm,
    evapPot). 

    It performs its computations solely from the evaporation forcing driven by
    climatic demand, limited by the coefficient of evaporation from the soil
    (kce).
    
    Note : difference in humectation of the top and bottom tanks is not taken
    into consideration in this approach.  The
  
    This function has been adapted from DemandeSol procedure, from bileau.pas
    and exmodules 1 & 2.pas file from the original FORTRAN code.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """
    # group 44
    data["evapPot"][j,:,:] = data["ET0"][j,:,:] * data["kce"][j,:,:]

    return data





def estimate_soil_evaporation(j, data):
    """
    This function computes estimation of soil evaporation (mm, evap). It uses
    the potential soil evaporation (evapPot) and the fraction of evaporable soil
    water (fesw), bounded by the surface tank stock.

    It has been adapted from the EvapRuSurf procedure, from bileau.pas and
    exmodules 1 & 2.pas file from the original FORTRAN code.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    #! replacing stRuSurf by surface_tank_stock
    #// data["evap"][j:,:,:] = np.minimum(data["evapPot"][j,:,:] * data["fesw"][j,:,:]**2, data["stRuSurf"][j,:,:])[...,np.newaxis]
    data["evap"][j:,:,:] = np.minimum(
        data["evapPot"][j,:,:] * data["fesw"][j,:,:]**2,
        data["surface_tank_stock"][j,:,:]
    )

    return data





def estimate_FEMcW_and_update_mulch_water_stock(j, data, paramITK):
    """
    This function calculates the fraction of evaporable water from the mulch
    (FEMcW).

    If the mulch water stock is greater than 0, then we compute FEMcW, which we
    consider to be equal to the filling ratio of the mulch water capacity. We
    then update the mulch water stock by removing the water height equivalent to
    the climate forcing demand, modulated by FEMcW and the plant cover (ltr).

    This function is adapted from the procedure EvapMC, from bileau.pas and
    exmodules 2.pas file from the original FORTRAN code.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramITK (_type_): _description_

    Returns:
        _type_: _description_
    """

    # group 45
    data["FEMcW"][j,:,:] = np.where(
        #! replacing stockMc with mulch_water_stock
        #// data["stockMc"][j,:,:] > 0,
        data["mulch_water_stock"][j,:,:] > 0,
        #! inverting the fraction to get stock over capacity, and not the other way round
        #// (paramITK["humSatMc"] * data["biomMc"][j,:,:] * 0.001) / data["stockMc"][j,:,:],
        data["mulch_water_stock"][j,:,:] / (paramITK["humSatMc"] * data["biomMc"][j,:,:] / 1000),
        data["FEMcW"][j,:,:],
    )

    # group 46
    #! replacing stockMc with mulch_water_stock
    #// data["stockMc"][j:,:,:] = np.maximum(
    data["mulch_water_stock"][j:,:,:] = np.maximum(
        0,
        #! removing the power of 2 in the equation
        #// data["stockMc"][j,:,:] - data["ltr"][j,:,:] * data["ET0"][j,:,:] * data["FEMcW"][j,:,:]**2,
        data["mulch_water_stock"][j,:,:] - (data["ltr"][j,:,:] * data["ET0"][j,:,:] * data["FEMcW"][j,:,:]**2),
    )

    return data





def estimate_ftsw(j, data):
    """
    This function estimates the fraction of evaporable soil water (fesw) from
    the root reservoir. 

    It is based on the EvalFTSW procedure, from the bileau.pas, exmodules 1 &
    2.pas, risocas.pas, riz.pas files from the original FORTRAN code.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
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
    )

    return data





def estimate_potential_plant_transpiration(j, data):
    """
    This function computes the potential transpiration from the plant.

    Computation is based on the climate forcing (ET0), as well as the kcp coefficient.

    This code is based on the DemandePlante procedure, from the bileau.pas, bhytypeFAO.pas, and
    exmodules 1 & 2.pas files from the original FORTRAN code.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """
    # ggroup 51
    data["trPot"][j,:,:] = (data["kcp"][j,:,:] * data["ET0"][j,:,:])
    
    return data




def estimate_kcTot(j, data):
    """
    This function computes the total kc coefficient.

    Computation is based on the kcp (transpiration coefficient) and kce
    (evaporation from the soil) coefficients. Where the crop coefficient is 0
    (meaning that there was no emergence yet), kcTot takes the value of kce.

    This function is based on the EvalKcTot procedure, from the bileau.pas and
    exmodules 1 & 2.pas files, from the original FORTRAN code.

    #! Note : code has been modified to match the original SARRA-H behavior.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    # added a condition on 19/08/22 to match SARRA-H original behavior
    data["kcTot"][j,:,:] = np.where(
        data["kcp"][j,:,:] == 0.0,
        data["kce"][j,:,:],
        data["kce"][j,:,:] + data["kcp"][j,:,:],
    )

    return data




def estimate_pFact(j, data, paramVariete):
    """_summary_

    This function computes the pFactor, which is a bound coefficient used in the
    computation of cstr from ftsw. This coefficient delimits the portion of the
    FTSW below which water stress starts to influence the transpiration.

    FAO reference for critical FTSW value for transpiration response (0 =
    stomata respond immediately if FTSW<1; 0.5 for most of the crops)

    pFact is bounded in [0.1, 0.8].

    For details see https://agritrop.cirad.fr/556855/1/document_556855.pdf

    This function is based on the CstrPFactor procedure, from bileau.pas,
    exmodules 1 & 2.pas, risocas.pas files, from the original FORTRAN code.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramVariete (_type_): _description_

    Returns:
        _type_: _description_
    """
    # group 53
    data["pFact"][j:,:,:] = paramVariete["PFactor"] + \
        0.04 * (5 - np.maximum(data["kcp"][j,:,:], 1) * data["ET0"][j,:,:])
    
    # group 54
    data["pFact"][j:,:,:] = np.minimum(
        np.maximum(
            0.1,
            data["pFact"][j,:,:],
        ),
        0.8,
    )

    return data




def estimate_cstr(j, data):
    """
    This function computes the water stress coefficient cstr.

    It uses ftsw and pFact. cstr is bounded in [0, 1].

    This function is based on the CstrPFactor procedure, from bileau.pas,
    exmodules 1 & 2.pas, risocas.pas files, from the original FORTRAN code.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """
    #group 55
    data["cstr"][j:,:,:] = np.minimum((data["ftsw"][j,:,:] / (1 - data["pFact"][j,:,:])), 1)
    # group 56
    data["cstr"][j:,:,:] = np.maximum(0, data["cstr"][j,:,:])

    return data




def estimate_plant_transpiration(j, data):
    """

    This function computes the transpiration from the plant.

    This function is based on the EvalTranspi procedure, from bileau.pas,
    bhytypeFAO.pas, exmodules 1 & 2.pas, from the original FORTRAN code.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """
    # group 58
    data["tr"][j:,:,:] = (data["trPot"][j,:,:] * data["cstr"][j,:,:])

    return data


def compute_evapotranspiration(j, data, paramITK, paramVariete):
    data = estimate_fesw(j, data) 
    data = estimate_kce(j, data, paramITK)
    data = estimate_soil_potential_evaporation(j, data)
    data = estimate_soil_evaporation(j, data)
    data = estimate_FEMcW_and_update_mulch_water_stock(j, data, paramITK)
    data = estimate_ftsw(j, data)
    data = estimate_kcp(j, data, paramVariete)
    data = estimate_potential_plant_transpiration(j, data)
    data = estimate_kcTot(j, data)
    data = estimate_pFact(j, data, paramVariete)
    data = estimate_cstr(j, data)
    data = estimate_plant_transpiration(j, data)
    return data




def estimate_transpirable_surface_water(j, data):
    """
    This function estimates the transpirable surface water. It removes
    1/10th of surface tank capacity as water is condidered as bound.
    This function is based on the ConsoResSep procedure, from bileau.pas,
    exmodules 1 & 2.pas files, from the original FORTRAN code.
    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    # group 59
    #! replacing stRuSurf by surface_tank_stock
    #! renaming ruSurf with surface_tank_capacity
    #// data["trSurf"][j:,:,:] = np.maximum(0, data["stRuSurf"][j,:,:] - data["ruSurf"][j,:,:] / 10)[...,np.newaxis]
    data["trSurf"][j:,:,:] = np.maximum(
        0,
        data["surface_tank_stock"][j,:,:] - data["surface_tank_capacity"] * 0.1,
    )
    return data




def apply_evaporation_on_surface_tank_stock(j, data):
    # qte d'eau evapore a consommer sur le reservoir de surface
    # group 60
    #! replacing stRuSurf by surface_tank_stock
    #// data["stRuSurf"][j:,:,:] = np.maximum(0, data["stRuSurf"][j,:,:] - data["evap"][j,:,:])[...,np.newaxis]
    data["surface_tank_stock"][j:,:,:] = np.maximum(0, data["surface_tank_stock"][j,:,:] - data["evap"][j,:,:])
    return data
    



def estimate_water_consumption_from_root_tank_stock(j, data):
    """
    This function estimates consoRur, which is the water to be consumed from
    the root tank stock.

    If soil evaporation (evap) is higher than transpirable surface water
    (trSurf), then consumption from root tank stock equals trSurf. Else, it
    equals evap.

    #? how to interpret this ?

    Args:
        j (_type_): _description_
        data (_type_): _description_
    """

    data["consoRur"][j:,:,:] = np.where(
        data["evap"][j,:,:] > data["trSurf"][j,:,:],
        data["trSurf"][j,:,:],
        data["evap"][j,:,:],
    )

    return data




def update_total_tank_stock_with_water_consumption(j, data):
    """
    This function updates the total tank stock by subtracting the lower water consumption
    value from estimate_water_consumption_from_root_tank_stock

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    # group 62
    #! renaming stTot to total_tank_stock
    #// data["stTot"][j:,:,:] = np.maximum(0, data["stTot"][j,:,:] - data["consoRur"][j,:,:])[...,np.newaxis]
    data["total_tank_stock"][j:,:,:] = np.maximum(0, data["total_tank_stock"][j,:,:] - data["consoRur"][j,:,:])#[...,np.newaxis]

    return data




def update_water_consumption_according_to_rooting(j, data):
    """
    This function updates the water consumption consoRur according to
    rooting depth.

    If the root tank capacity is lower than the surface tank capacity,
    meaning than the roots did not dive into the deep tank yet, then the
    water consumption is updated to equal the evaporation at the prorata of
    the exploration of surface tank by the roots.

    Else, consoRur keeps it value, which was previously computed by
    estimate_water_consumption_from_root_tank_stock.

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    #  fraction d'eau evapore sur la part transpirable qd les racines sont moins
    #  profondes que le reservoir de surface, mise a jour des stocks transpirables
    # group 63

    data["consoRur"][j:,:,:] = np.where(
        #! renaming stRurMax with root_tank_capacity
        #! renaming ruSurf with surface_tank_capacity
        #// data["stRurMax"][j,:,:] < data["ruSurf"][j,:,:],
        data["root_tank_capacity"][j:,:,:] < data["surface_tank_capacity"],
        #! renaming stRur to root_tank_stock
        #! renaming ruSurf with surface_tank_capacity
        #// data["evap"][j,:,:] * data["stRur"][j,:,:] / data["ruSurf"][j,:,:],
        data["evap"][j,:,:] * data["root_tank_stock"][j,:,:] / data["surface_tank_capacity"],
        data["consoRur"][j,:,:],
    )

    return data




def update_root_tank_stock_with_water_consumption(j, data):
    """
    This function updates root tank stock according to water consumption.
    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    # group 64
    #! renaming stRur to root_tank_stock
    #// data["stRur"][j:,:,:] = np.maximum(0, data["stRur"][j,:,:] - data["consoRur"][j,:,:])#[...,np.newaxis]
    data["root_tank_stock"][j:,:,:] = np.maximum(0, data["root_tank_stock"][j,:,:] - data["consoRur"][j,:,:])
    return data




def update_plant_transpiration(j, data):
    """
    reajustement de la qte transpirable considerant que l'evap a eu lieu avant
    mise a jour des stocks transpirables  
    if plant transpiration is higher than the root tank stock, then plant 
    transpiration is updated to be equal to the difference between the root tank stock and the
    plant transpiration. Else, its value is unmodified.
    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
   
    # group 65
    data["tr"][j:,:,:] = np.where(
        #! renaming stRur to root_tank_stock
        #// data["tr"][j,:,:] > data["stRur"][j,:,:],
        data["tr"][j,:,:] > data["root_tank_stock"][j,:,:],
        #// np.maximum(data["stRur"][j,:,:] - data["tr"][j,:,:], 0),
        np.maximum(data["root_tank_stock"][j,:,:] - data["tr"][j,:,:], 0),
        data["tr"][j,:,:],
    )
    return data




def update_surface_tank_stock_according_to_transpiration(j, data):
    """
    This function updates the surface tank stock to reflect plant
    transpiration.

    if the root tank stock is above 0, then surface tank stock is updated by
    subtracting the plant transpiration modulated by the ratio between the
    transpirable water and the root tank stock.

    That is to say, the more transpirable water is close to the root tank stock,
    the more of transpirated water by plant will be removed from surface tank stock.
 
    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

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
        np.maximum(
            data["surface_tank_stock"][j,:,:] - \
                (data["tr"][j,:,:] * np.minimum(data["trSurf"][j,:,:]/data["root_tank_stock"][j,:,:], 1)),
            0,
        ),
        #// data["stRuSurf"][j,:,:],
        data["surface_tank_stock"][j,:,:],
    )

    return data





def update_root_tank_stock_with_transpiration(j, data):
    """_summary_
    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    # group 67
    #! renaming stRur to root_tank_stock
    #// data["stRur"][j:,:,:] = np.maximum(0, data["stRur"][j,:,:] - data["tr"][j,:,:])#[...,np.newaxis]
    data["root_tank_stock"][j:,:,:] = np.maximum(0, data["root_tank_stock"][j,:,:] - data["tr"][j,:,:])#[...,np.newaxis]
    return data





def update_total_tank_stock_with_transpiration(j, data):
    # data["stRu"][j:,:,:] = np.maximum(0, data["stRu"][j,:,:] - data["tr"][j,:,:])
    # essais stTot
    # group 68
    #! renaming stTot to total_tank_stock
    #// data["stTot"][j:,:,:] = np.maximum(0, data["stTot"][j,:,:] - data["tr"][j,:,:])#[...,np.newaxis] 
    data["total_tank_stock"][j:,:,:] = np.maximum(0, data["total_tank_stock"][j,:,:] - data["tr"][j,:,:])#[...,np.newaxis] ## ok
    return data





def update_etr_etm(j, data):
    # group 69
    data["etr"][j:,:,:] = (data["tr"][j,:,:] + data["evap"][j,:,:]).copy()#[...,np.newaxis]
    
    # group 70
    data["etm"][j:,:,:] = (data["trPot"][j,:,:] + data["evapPot"][j,:,:]).copy()#[...,np.newaxis]
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

    data = estimate_transpirable_surface_water(j, data)

    data = apply_evaporation_on_surface_tank_stock(j, data)

    data = estimate_water_consumption_from_root_tank_stock(j, data)

    data = update_total_tank_stock_with_water_consumption(j, data)

    data = update_water_consumption_according_to_rooting(j, data)

    data = update_root_tank_stock_with_water_consumption(j, data)

    data = update_plant_transpiration(j, data)

    data = update_surface_tank_stock_according_to_transpiration(j, data)

    data = update_root_tank_stock_with_transpiration(j, data)

    data = update_total_tank_stock_with_transpiration(j, data)

    data = update_etr_etm(j, data)

    return data