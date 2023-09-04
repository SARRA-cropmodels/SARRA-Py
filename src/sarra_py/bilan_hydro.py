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
    This function initializes the root tank.

    If during the considered day j there are pixels in phase 1 (initialisation),
    we test for pixels at phase change between phases 0 and 1 ('changePhase = 1'
    and 'numPhase = 1').

    On these pixels, the maximum root tank water storage ('root_tank_capacity',
    mm) is initialised by multiplying the initial root depth ('profRacIni', mm)
    with the soil water storage capacity ('ru', mm/m). This value is broadcasted
    on the time series. For every other day in the cycle where there are pixels
    at , the value remains unchanged.

    https://docs.google.com/presentation/d/1QHhbNjF9ysCG_yZzWXb7ns0vOFlGfNhYw8AYrotm0fY/edit#slide=id.g27a6b3e8a72_0_30

    Args:
        j (int): day identifier
        data (xarray dataset): an xarray dataset of dimensions (day, width,
        height) containing the variables 'numPhase', 'root_tank_capacity',
        'changePhase', 'ru'
        paramITK (dict): a dictionary containing the ITK parameter 'profRacIni'

    Returns:
        _type_: _description_
    """
    if np.any(data["numPhase"][j,:,:] == 1) :
        data["root_tank_capacity"][j:,:,:] = xr.where(
            (data["changePhase"][j,:,:] == 1) & (data["numPhase"][j,:,:] == 1),
            paramITK["profRacIni"] / 1000 * data["ru"],
            data["root_tank_capacity"][j,:,:],
        )

    return data



def initialize_delta_root_tank_capacity(j, data):
    """
    This function initializes the daily variation in root tank capacity. 

    This variable represents daily variation in water height accessible to
    roots, in mm.

    For each pixel at a developmental stage different from zero, and that is not
    at initialization phase ('changePhase = 1' and 'numPhase = 1'), the daily
    variation in root tank capacity (delta_root_tank_capacity, mm) is updated.
    
    The updated value depends on the daily root growth speed (itself depending
    on the current development phase of the plant), the drought stress
    coefficient ('cstr'), and the soil water storage capacity ('ru', mm/m). 

    https://docs.google.com/presentation/d/1QHhbNjF9ysCG_yZzWXb7ns0vOFlGfNhYw8AYrotm0fY/edit#slide=id.g27a6b3e8a72_0_118
    
    However, when 'root_tank_capacity' is above 'surface_tank_capacity'
    (meaning that the roots are prospecting water deeper than the surface tank),
    the daily root capacity variation is calculated as the product of soil water
    storage capacity ('ru'), the daily root growth speed ('vRac'), and a
    coefficient made from 'cstr' shifted by 0.3, capped at 1.0. 

    https://docs.google.com/presentation/d/1QHhbNjF9ysCG_yZzWXb7ns0vOFlGfNhYw8AYrotm0fY/edit#slide=id.g27a6b3e8a72_0_71

    That is to say, when roots are going deep, the root growth speed is
    modulated by drought stress.

    The drought stress coefficient 'cstr' measures the level of drought stress
    with 0 being full stress. The root growth speed is assumed to remain
    non-null during a drought stress as a matter of survival, with a certain
    level of tolerance given by the [0.3, 1] bound of the coefficient. Using the
    [0.3, 1] bound is a way to tell that in the [0.7, 1] 'cstr' interval, there
    is no effect of drought stress on the root growth speed, allowing for a
    certain level of tolerance of the plant.
    
    When 'root_tank_capacity' is lower than 'surface_tank_capacity', the root growth
    speed is not modulated by drought stress.
    
    Args:
        j (int): The current iteration step of the process.
        data (xarray.Dataset): The input data containing relevant information.

    Returns:
        xarray.Dataset: The updated input data with the daily root capacity variation calculated and stored.
    """

    condition = (data["numPhase"][j,:,:] > 0) & \
        np.invert((data["numPhase"][j,:,:] == 1) & (data["changePhase"][j,:,:] == 1))

    data["delta_root_tank_capacity"][j,:,:] = xr.where(
        condition,
        xr.where(
            (data["root_tank_capacity"][j,:,:] > data["surface_tank_capacity"]),
            (data["vRac"][j,:,:] * np.minimum(data["cstr"][j,:,:] + 0.3, 1.0)) / 1000 * data["ru"],
            data["vRac"][j,:,:] / 1000 * data["ru"],
        ),
        data["delta_root_tank_capacity"][j,:,:],
    )

    return data




def update_delta_root_tank_capacity(j, data):
    """
    This function updates the daily variation in root tank capacity
    (delta_root_tank_capacity, mm) depending on the water height to humectation
    front (hum, mm) and the root tank capacity (root_tank_capacity, mm).
    
    For each pixel at a developmental stage different from zero, and that is not
    at initialization phase ('changePhase = 1' and 'numPhase = 1'), when the
    difference between the water height to humectation front (hum, mm) and the
    root_tank_capacity is less than the delta_root_tank_capacity (meaning that
    the daily variation in root tank capacity is higher that the height of water
    necessary to reach the height of water of the humectation front),
    delta_root_tank_capacity is updated to be equal to the difference between
    the water height to humectation front and the root_tank_capacity.
    
    In other words, the change in root tank capacity delta_root_tank_capacity is
    limited by the water height to humectation front. Which can be interpreted as :
    the roots cannot grow deeper than the humectation front.

    ? ...which means the humectation from has to be updated somewhere ?
    
    For any other day or if root_tank_capacity is above
    delta_root_tank_capacity, delta_root_tank_capacity value is unchanged.

    https://docs.google.com/presentation/d/1QHhbNjF9ysCG_yZzWXb7ns0vOFlGfNhYw8AYrotm0fY/edit#slide=id.g27a6b3e8a72_0_161

    Args:
        j (_type_): _description_
        data (_type_): _description_
    """

    condition = (data["numPhase"][j,:,:] > 0) & \
        np.invert((data["numPhase"][j,:,:] == 1) & (data["changePhase"][j,:,:] == 1))

    data["delta_root_tank_capacity"][j:,:,:] = np.where(
        condition,   
        np.where(
            (data["humectation_front"][j,:,:] - data["root_tank_capacity"][j,:,:]) < data["delta_root_tank_capacity"][j,:,:],
            data["humectation_front"][j,:,:] - data["root_tank_capacity"][j,:,:],
            data["delta_root_tank_capacity"][j,:,:],
        ),
        data["delta_root_tank_capacity"][j,:,:],
    )

    return data




def update_root_tank_capacity(j, data):
    """
    This function updates the root tank capacity (root_tank_capacity, mm) by
    adding the daily variation in root tank capacity.
    
    For each pixel at a developmental stage different from zero, and that is not
    at initialization phase ('changePhase = 1' and 'numPhase = 1'),
    root_tank_capacity is updated to be summed with the change in root water
    storage capacity delta_root_tank_capacity.
    
    In other words, root_tank_capacity is incremented by the change in root
    water storage capacity related to root growth. Easy, right ?

    https://docs.google.com/presentation/d/1QHhbNjF9ysCG_yZzWXb7ns0vOFlGfNhYw8AYrotm0fY/edit#slide=id.g27a6b3e8a72_0_238

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    condition = (data["numPhase"][j,:,:] > 0) & \
        np.invert((data["numPhase"][j,:,:] == 1) & (data["changePhase"][j,:,:] == 1))

    data["root_tank_capacity"][j:,:,:] = np.where(
        condition,
        data["root_tank_capacity"][j,:,:] + data["delta_root_tank_capacity"][j,:,:],
        data["root_tank_capacity"][j,:,:],
    )

    return data




def update_root_tank_stock(j, data):
    """
    This functions update the quantity of water of the root tank ('root_tank_stock', mm).
        
    For each pixel at a developmental stage different from zero, and that is not
    at initialization phase ('changePhase = 1' and 'numPhase = 1'), and for
    which the 'root_tank_capacity' is greater than 'surface_tank_capacity' (meaning
    that roots go beyond the surface water storage capacity), 'root_tank_stock'
    is incremented by delta_root_tank_capacity.
    
    However, if 'root_tank_capacity' is lesser than 'surface_tank_capacity' (meaning
    that roots do not plunge into the deep reservoir), 'root_tank_stock' is
    updated to be equal to surface_tank_stock minus 1/10th of the
    surface_tank_capacity, multiplied by the ratio between root_tank_capacity
    and surface_tank_capacity. That is to say "we take at the prorata of depth
    and surface stock".
    
    For any other day, root_tank_stock is unchanged.

    ? Why is the tank stock incremented instead of root tank capacity ? If the
    ? root tank capacity is incremented, that makes sense as we add to the root
    ? tank capacity the capacity newly gained through delta_root_tank_capacity.
    ? There is no sense in incrementing the root tank stock with the
    ? delta_root_tank_capacity, as the delta root tank capacity, representing
    ? growing of roots is independant of the quantity of water in the soil.
    ? However, the delta root tank capacity is blocked by hum the humidity front.
    ? Still, humidity front only grows and limits the maximum growth of roots, and
    ? is not involved in root water stock.
 
    ? Also, if the roots do not go in the deep reservoir, there is an increase in
    ? root tank stock. Considering this is a mistake and that root_tank_capacity
    ? should be increased, this would mean root tank capacity is increased by a
    ? value that depends on the filling of the surface tank first
    ? (surface_tank_stock minus 1/10th of the surface_tank_capacity, that would be
    ? about the bound water), times the ratio between root_tank_capacity and
    ? surface_tank_capacity. This would mean if when there is few roots the
    ? increase in root tank capacity is small, and if roots are close to passing
    ? into the deep reservoir, the increase in root tank capacity nears the
    ? surface_tank_stock. Again, there is no sense in increasing the root tank
    ? capacity with such value however this would be ok for root_tank_stock...
 
    ? Overall there seems to be a mixup between the objectives of the two parts of
    ? this function ?
 
    ? at the moment this function is applied, root_tank_capacity is already
    ? updated to take into consideration the root growth from the day, limited by
    ? both the water stress and the depth of the humectation front. i still do not
    ? understand why we would increase root tank stock, as we do not have
    ? supplementary water. it would be like creating water from nowhere.
 
    ? so until further notice i will let this function as it is, but i will keep
    ? in mind that it is probably wrong.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    condition = (data["numPhase"][j,:,:] > 0) & \
        np.invert((data["changePhase"][j,:,:] == 1) & (data["numPhase"][j,:,:] == 1)),
    

    data["root_tank_stock"][j:,:,:] = xr.where(
        condition,
        xr.where(
            (data["root_tank_capacity"][j,:,:] > data["surface_tank_capacity"]),
            data["root_tank_stock"][j,:,:] + data["delta_root_tank_capacity"][j,:,:],
            np.maximum(
                ((data["surface_tank_stock"][j,:,:] - data["surface_tank_capacity"] * 1/10) * \
                (data["root_tank_capacity"][j,:,:] / data["surface_tank_capacity"])),
                0),
        ).expand_dims("time", axis=0), 
        
        data["root_tank_stock"][j,:,:],
    )

    return data


def EvolRurCstr2(j, data, paramITK):

    """
    This function is a legacy wrapper for the functions related to the
    calculation of the root tank capacity and stock.

    It has been translated from the procedure EvolRurCstr2, of the original
    Pascal codes bileau.pas.

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
    """

    data = initialize_root_tank_capacity(j, data, paramITK)
    data = initialize_delta_root_tank_capacity(j, data)
    data = update_delta_root_tank_capacity(j, data)
    data = update_root_tank_capacity(j, data)
    data = update_root_tank_stock(j, data) #! we keep this function for now even though it is probably wrong, it will need further screening

    return data




####################### list of functions for rempliRes #######################




def update_previous_humectation_front_at_end_of_season(j, data):
    """
    This function saves information about the water height to humectation front
    to another variable (previous_humectation_front, mm) at the end of season so
    it can be used in the next cycle.

    previous_humectation_front is initialized in the function InitPlotMc, and
    set to be equal to hum. hum itself is initialized to take the maximum value
    between surface_tank_capacity, root_tank_capacity and total_tank_stock.

    At the harvest date (numPhase = 7), the previous_humectation_front variable
    is set to equal the highest value between hum (mm, water height to
    humectation front) and surface_tank_capacity (mm). This value is broadcasted
    over the time dimension.

    At any other point in time, its value is unchanged.

    Args:
        j (int): number of the day
        data (xarray dataset): _description_
    Returns:
        xarray dataset: _description_
    """
    condition = (data["numPhase"][j,:,:] == 7) & (data["changePhase"][j,:,:] == 1)

    data["previous_humectation_front"][j:,:,:] = np.where(
        condition,
        np.maximum(data["humectation_front"][j,:,:], data["surface_tank_capacity"]),
        data["previous_humectation_front"][j,:,:],
    )

    return data





def update_humectation_front_at_end_of_season(j, data):
    """
    This function updates the value of water height to humectation front
    (humectation_front, mm) at the end of season.

    At the harvest date (numPhase = 7), the humectation_front variable is set to
    equal the surface_tank_capacity (mm). This value is broadcasted over the
    time dimension.

    At any other point in time, its value is unchanged.

    ? The way of resetting the humectation_front at harvest date hasn't a real
    ? agronomical meaning. This function allows for resetting the variable at an
    ? initial state.

    ? However it is a way to say that when the plant dies, the new ones will have
    ? to make up their new humectation fronts starting again from surface_tank_capacity

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    condition = (data["numPhase"][j,:,:] == 7) & (data["changePhase"][j,:,:] == 1)

    data["humectation_front"][j:,:,:] = np.where(
        condition,
        data["surface_tank_capacity"],
        data["humectation_front"][j,:,:],
    )

    return data





def update_root_tank_capacity_at_end_of_season(j, data):
    """
    This function saves information about the root_tank_capacity to another
    variable (previous_root_tank_capacity, mm) at the end of season so it
    can be used in the next cycle.

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    condition = (data["numPhase"][j,:,:] == 7) & (data["changePhase"][j,:,:] == 1)

    data["previous_root_tank_capacity"][j:,:,:] = np.where(    
        condition,
        data["root_tank_capacity"][j,:,:],
        data["previous_root_tank_capacity"][j,:,:],
    )
    return data





def update_previous_root_tank_stock_at_end_of_season(j, data):
    """
    This function updates the value of previous stock of water in the root tank
    (previous_root_tank_stock, mm) at the end of season.

    When the phase changes from 7 to 1, previous_root_tank_stock is set to equal
    the ratio between root_tank_stock and root_tank_capacity, that is to say the
    filling rate of the root reservoir. Otherwise, it stays at its initial value
    of 0. Its value is broadcasted along j. previous_root_tank_stock is
    initialized with a value of 0.

    ? The way of resetting the previous_root_tank_stock at harvest date hasn't a real
    ? agronomical meaning.

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """

    condition = (data["numPhase"][j,:,:] == 7) & (data["changePhase"][j,:,:] == 1)
    data["previous_root_tank_stock"][j:,:,:] = np.where(
        condition,
        data["root_tank_stock"][j,:,:] / data["root_tank_capacity"][j,:,:],
        data["previous_root_tank_stock"][j,:,:],
    )
    return data





def update_previous_total_tank_stock_at_end_of_season(j, data):
    """
    This function updates the value of previous total stock of water
    (previous_total_tank_stock, mm) at the end of season.

    When the phase changes from 7 to 1, previous_total_tank_stock is set to equal
    the difference between total_tank_stock and surface_tank_stock.

    Otherwise, it stays at its initial value of 0. Its value is broadcasted
    along j. previous_total_tank_stock is initialized with a value of 0.

    ? The way of resetting the previous_total_tank_stock at harvest does not seem to have a real
    ? agronomical meaning.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    condition = (data["numPhase"][j,:,:] == 7) & (data["changePhase"][j,:,:] == 1)

    data["previous_total_tank_stock"][j:,:,:] = np.where(
        condition,
        data["total_tank_stock"][j,:,:] - data["surface_tank_stock"][j,:,:], # essai stTot #? what is that ?
        data["previous_total_tank_stock"][j,:,:],
    )

    return data





def reset_total_tank_capacity(j, data):
    """
    This function resets the value total_tank_capacity at each loop.
    
    ? Why redfining stRuMax at each loop ? Neither ru, profRu 
    ? nor total_tank_capacity are modified during the simulation.
    ? At the same time, its value is initialized at 0, and this function 
    ? is the only place where it is initialized taking ru and profRu into account.

    ? We modify it so it runs only at day one.
    ? But it should be moved to the initialization part of the code.

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    if j == 0:
        data["total_tank_capacity"][j:,:,:] = (data["ru"] * data["profRu"] / 1000)
    
    return data





def update_surface_tank_stock(j, data):
    """
    This function updates the value of water stock in the surface tank
    (surface_tank_stock, mm) with the water available for the day
    (available_water, mm), within the limits of 110% surface_tank_capacity.
    
    We update surface_tank_stock by adding the available_water, which as this
    point in the process list corresponds to the water available from 1) rain,
    2) irrigation for the day, corrected from 3) intake by mulch (fill_mulch
    function), and 4) runoff (compute_runoff). However, we do not allow
    surface_tank_stock to exceed 110% of the surface_tank_capacity.

    ? This means it is possible that the surface tank fill rate is above 100%,
    ? which is a rather strange assumption.

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """
    data["surface_tank_stock"][j:,:,:] = np.minimum(
        data["surface_tank_stock"][j,:,:] + data["available_water"][j,:,:],
        1.1 * data["surface_tank_capacity"]
    )
    return data





def estimate_transpirable_water(j, data):
    """
    This function estimates the daily height of water available from the surface
    reservoir for transpiration by the plant ('eauTranspi', mm).

    If the filling rate of the surface tank ('surface_tank_stock' /
    'surface_tank_capacity') for the previous day is under 10%, we set the
    quantity of transpirable water as the water available for the day
    ('eauDispo') minus the water height necessary to keep the filling rate of
    the surface tank at 10%. 
    
    Said otherwise, a part of the water available for the day ('eauDispo') is used
    to maintain the surface reservoir at a minimum level of 10% of its capacity,
    as this water is considered as bound to the surface reservoir and cannot be
    transpired. 

    Of course, if the filling rate of the previous day is above 10%, the transpirable
    water is equal to the water available for the day.

    Furthermore, transpirable water cannot be negative.

    ? Remark : if the use of j-1 indices is troublesome, it should be feasible to
    ? run this function just before update_surface_tank_stock.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    # data["eauTranspi"][j,:,:] = np.where(
    #     data["surface_tank_stock"][j-1,:,:] < 0.1 * data["surface_tank_capacity"],
    #     np.maximum(
    #         0,
    #         data["available_water"][j,:,:] - (0.1 * data["surface_tank_capacity"] - data["surface_tank_stock"][j-1,:,:])
    #         ),
    #     data["available_water"][j,:,:],
    # )

    #! simplification : we are already working with water height between permanent wilting point and field capacity,
    #! so there is no need to consider bound water as this is already taken into consideration in the calculation of RU
    #! if we want to take this further correctly we have to rewrite everything, so better keep it simple for now

    data["eauTranspi"][j,:,:] = data["available_water"][j,:,:]

    return data





def update_total_tank_stock(j, data):
    """
    This functions updates the total height of transpirable water
    ('total_tank_stock', mm) with the amount of transpirable water for the day
    ('eauTranspi', mm). 

    ? Said differently, 'total_tank_stock' represents the total amount of water
    ? available for the plant in the soil column ?

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    data["total_tank_stock"][j:,:,:] = (data["total_tank_stock"][j,:,:] + data["eauTranspi"][j,:,:])

    return data





def update_delta_total_tank_stock(j, data):
    """
    This function estimates the positive variation of the total height of
    transpirable water ('delta_total_tank_stock', mm).

    It is computed as the difference between the total_tank_stock and
    previous_total_tank_stock, bound in 0. 
    
    'previous_total_tank_stock' is initialized to be equal to 'total_tank_stock'
    at the beginning of the simulation. As 'total_tank_stock' is initialized
    with the 'stockIrr' parameter, simulations should start with a 0 value.

    'previous_total_tank_stock' is updated each day with the 'update_struprec'
    function.
    
    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """

    data["delta_total_tank_stock"][j:,:,:] = np.maximum(0, data["total_tank_stock"][j,:,:] - data["previous_total_tank_stock"][j,:,:])
    return data





def update_total_tank_stock_for_second_crop_cycle(j, data):
    """
    This function updates the total height of transpirable water
    ('total_tank_stock', mm), specifically if a second crop cycle starts.

    This update is applied only if a second crop cycle starts, as
    previous_root_tank_capacity and previous_total_tank_stock are initialized as
    null. That means conditions 2 and 3 of this function will fail during a
    first crop cycle, leading to no change in total_tank_stock.
    
    However, at numPhase = 7, which corresponds to the harvesting date and that
    opens the possibility for a second crop cycle, previous_root_tank_capacity
    and previous_total_tank_stock will be updated.

    From now on, if delta_total_tank_stock is greater than humectation front
    (condition 1 passed), and previous_root_tank_capacity is greater or equal to
    the humectation_front (condition 2 passed), and if the humectation_front is
    below previous_humectation_front (condition 3 passed), then the total tank
    stock is updated to be increased with the difference between
    delta_total_tank_stock and humectation_front, times the previous root tank
    stock.  

    Thus, if the root tank is empty, total_tank_stock will remain unchanged, and
    if the root tank is full, total_tank_stock will be increased up to the
    amount of water making the difference between quantity of water for
    humectation front and the variation in daily transpirable water.

    Also, if delta_total_tank_stock is greater than humectation front (condition
    1 passed), but previous_root_tank_capacity is lower than the
    humectation_front (condition 2 failed), while the humectation_front is below
    previous_humectation_front (condition 3 passed), we update the total tank
    stock to be equal to delta_total_tank_stock.

    In other words, if during the second crop cycle the humectation front is too
    low, we increase the total tank stock.

    ? To my opinion, this function is way too complicated for a borderline use case
    ? (multiple cropping cycles during one simulation).
    ? We'd want to keep the code for legacy reasons but if really this simulation
    ? feature is needed we'll have to simplify it.
 
    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    condition_1 = (data["delta_total_tank_stock"][j,:,:] > data["humectation_front"][j,:,:])
    condition_2 = (data["humectation_front"][j,:,:] <= data["previous_root_tank_capacity"][j,:,:])
    condition_3 = (data["humectation_front"][j,:,:] < data["previous_humectation_front"][j,:,:])

    data["total_tank_stock"][j:,:,:] = np.where(
        condition_1,
        np.where(
            condition_2, 
            data["total_tank_stock"][j,:,:] + (data["delta_total_tank_stock"][j,:,:] - data["humectation_front"][j,:,:]) * \
                  data["previous_root_tank_stock"][j,:,:],
            np.where(
                condition_3,
                data["delta_total_tank_stock"][j,:,:],
                data["total_tank_stock"][j,:,:],
            ),
        ),
        data["total_tank_stock"][j,:,:],
    )

    return data






def update_previous_total_tank_stock_for_second_crop_cycle(j, data):
    """
    This function performs the update of the previous total height of
    transpirable water (previous_total_tank_stock, mm).

    It will decrease the previous_total_tank_stock depending on the variation of
    transpirable water and height of humectation front.

    This update is applied only if a second crop cycle starts, as
    previous_root_tank_capacity and previous_total_tank_stock are initialized as
    null. That means conditions 2 and 3 of this function will fail during a
    first crop cycle, leading to no change in previous_total_tank_stock.

    In this function, if the variation of transpirable water
    (delta_total_tank_stock) increases above humectation_front (condition 1
    passed), and if humectation_front is above the previous_root_tank_capacity
    (condition failed), and if the depth of humectation front has decreased
    since the previous day (condition 3 passed), then previous_total_tank_stock
    equals 0.

    Starting from second simulation season (previous_root_tank_capacity != 0),
    if the variation of transpirable water (delta_total_tank_stock) increases
    above the depth of humectation front (hum), and if the depth of humectation
    front stays below or equel to the total soil capacity (conditions 1 and 2
    passed), then we decrease the value of previous_total_tank_stock by a the
    difference of water height between the variation of total tank stock
    (delta_total_tank_stock) and the depth of humectation front (hum),
    proportionally to the filling of the root tank capacity of previous season
    (previous_root_tank_stock). Thus, if the root tank is empty,
    previous_total_tank_stock will remain unchanged, and if the root tank is
    full, previous_total_tank_stock will be decreased up to the amount of water
    making the difference between quantity of water for humectation front and
    the variation in daily transpirable water.

    ? To my opinion, this function is way too complicated for a borderline use case
    ? (multiple cropping cycles during one simulation).
    ? We'd want to keep the code for legacy reasons but if really this simulation
    ? feature is needed we'll have to simplify it.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    condition_1 = (data["delta_total_tank_stock"][j,:,:] > data["humectation_front"][j,:,:])
    condition_2 = (data["humectation_front"][j,:,:] <= data["previous_root_tank_capacity"][j,:,:])
    condition_3 = (data["humectation_front"][j,:,:] < data["previous_humectation_front"][j,:,:])

    data["previous_total_tank_stock"][j:,:,:] = np.where(
        condition_1,
        np.where(
            condition_2,
            np.maximum(0, data["previous_total_tank_stock"][j,:,:] - (data["delta_total_tank_stock"][j,:,:] - data["humectation_front"][j,:,:]) * \
                       data["previous_root_tank_stock"][j,:,:]),
            np.where(
                condition_3,
                0,
                data["previous_total_tank_stock"][j,:,:],
            ),
        ),
        data["previous_total_tank_stock"][j,:,:],
    )

    return data





def update_delta_total_tank_stock_step_2(j, data):
    """
    ? Ok the logic is the same as for the two previous functions 
    ? and i don't want to document it as it is way too complicated
    ? and we won't be using it for now.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """
    condition_1 = (data["delta_total_tank_stock"][j,:,:] > data["humectation_front"][j,:,:])
    condition_2 = (data["humectation_front"][j,:,:] <= data["previous_root_tank_capacity"][j,:,:])
    condition_3 = (data["humectation_front"][j,:,:] < data["previous_humectation_front"][j,:,:])

    data["delta_total_tank_stock"][j:,:,:] = np.where(
        condition_1,
        np.where(
            condition_2,
            data["delta_total_tank_stock"][j,:,:] + (data["delta_total_tank_stock"][j,:,:] - data["humectation_front"][j,:,:]) * data["previous_root_tank_stock"][j,:,:],
            np.where(
                condition_3,
                data["delta_total_tank_stock"][j,:,:] + data["previous_total_tank_stock"][j,:,:],
                data["delta_total_tank_stock"][j,:,:],   
            ),
        ),
        data["delta_total_tank_stock"][j,:,:],
    )

    return data





def apply_humectation_front_boundaries(j, data):
    """
    This function updates the water height to humectation front
    (humectation_front, mm) by bounding it between delta_total_tank_stock and
    total_tank_capacity.
    
    That is to say depth of humectation front can only increase, and that
    humectation front can not go down indefinitely.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    data["humectation_front"][j:,:,:] = np.maximum(data["delta_total_tank_stock"][j,:,:], data["humectation_front"][j,:,:])
    data["humectation_front"][j:,:,:] = np.minimum(data["total_tank_capacity"][j,:,:], data["humectation_front"][j,:,:])

    return data





def update_drainage(j, data):
    """
    This function estimates the daily drainage (dr).
    
    When total tank overflows (total_tank_stock > total_tank_capacity), the
    drainage is computed from the difference between total_tank_stock and
    total_tank_capacity. This means the drainage value will be positive

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """

    condition = (data["total_tank_stock"][j,:,:] > data["total_tank_capacity"][j,:,:])

    data["drainage"][j,:,:] = np.where(
        condition,
        data["total_tank_stock"][j,:,:] - data["total_tank_capacity"][j,:,:],
        0,
    )
    return data





def update_total_tank_stock_after_drainage(j, data):
    """
    This function updates the total tank stock (total_tank_stock, mm) when these is overflowing.

    When capacity of total_tank_stock is exceeded, total_tank_stock value is replaced with 
    total_tank_capacity 

    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """

    condition = (data["total_tank_stock"][j,:,:] > data["total_tank_capacity"][j,:,:])

    data["total_tank_stock"][j:,:,:] = np.where(  
        condition,
        data["total_tank_capacity"][j,:,:],
        data["total_tank_stock"][j,:,:],
    )
    return data





def update_humectation_front_after_drainage(j, data):
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

    data["humectation_front"][j:,:,:] = np.maximum(data["humectation_front"][j,:,:], data["total_tank_stock"][j,:,:])

    return data




def compute_drainage(j, data):
    """
    This wrapper function aims to regroup computations related to drainage :
    - update_drainage
    - update total_tank_stock
    - update_humectation_front_after_drainage


    Args:
        j (_type_): _description_
        data (_type_): _description_
    """

    data = update_drainage(j, data)
    data = update_total_tank_stock_after_drainage(j, data)
    data = update_humectation_front_after_drainage(j, data)

    return data





def update_root_tank_stock_step_2(j, data):
    """
    This function updates the height of water in the tank of water accessible to
    roots ("root_tank_stock", mm).

    It increments root_tank_stock with transpirable water (eauTranspi), within
    the bounds of root_tank_capacity and total_tank_stock.

    This means the sum of transpirable water and root tank stock for the day
    firstly cannot be higher than the root tank capacity, which is fine to represent 
    the height of water accessible to roots. But also, that this sum limited by
    the root tank capacity cannot be higher than the total tank stock, which seems unlikely.  

    ? This raises the question about where does the potential water in excess go.


    Args:
        j (_type_): _description_
        data (_type_): _description_
    Returns:
        _type_: _description_
    """

    data["root_tank_stock"][j:,:,:] = np.minimum(data["root_tank_stock"][j,:,:] + data["eauTranspi"][j,:,:], data["root_tank_capacity"][j,:,:])
    data["root_tank_stock"][j:,:,:] = np.minimum(data["root_tank_stock"][j,:,:], data["total_tank_stock"][j,:,:])
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

    ! simplification : we want to simplify the code, and we don't want to keep the possibility of multiple crop cycles
    ! we keep the old code for maintainance and future developments though
    """

    #! simplification
    #// section 1 : updating the end_of_season memory variables
    #// in order to save resources, we test if there is at least one pixel at phase 7
    #// and one pixel at changePhase 1 in the current time step before applying the "end_of_season" functions
    #// if (np.any(data["numPhase"][j,:,:] == 7)) & (np.any(data["changePhase"][j,:,:] == 1)):
    #//     data = update_previous_humectation_front_at_end_of_season(j, data)
    #//     data = update_humectation_front_at_end_of_season(j, data)
    #//     data = update_root_tank_capacity_at_end_of_season(j, data)
    #//     data = update_previous_root_tank_stock_at_end_of_season(j, data)
    #//     data = update_previous_total_tank_stock_at_end_of_season(j, data)
    
    #! simplification
    #// we let this function here, conditioned to work for j0 only, but it should be moved into initialization
    data = reset_total_tank_capacity(j, data)

    # Updates the value of water stock in the surface tank (surface_tank_stock,
    # mm) with the water available for the day (available_water, mm), within the
    # limits of 110% surface_tank_capacity.
    data = update_surface_tank_stock(j, data)

    # Estimates the daily height of water available from the surface reservoir
    # for transpiration by the plant ('eauTranspi', mm). A part of the water
    # available for the day ('eauDispo') is used to maintain the surface
    # reservoir at a minimum level of 10% of its capacity, as this water is
    # considered as bound to the surface reservoir and cannot be transpired. 
    data = estimate_transpirable_water(j, data)

    # Updates the total height of transpirable water ('total_tank_stock', mm)
    # with the amount of transpirable water for the day ('eauTranspi', mm)
    data = update_total_tank_stock(j, data)

    #! simplification
    #// delta_total_tank_stock is used with second cycle computations
    #// estimating positive delta between total_root_tank and stRuPrec
    #// data = update_delta_total_tank_stock(j, data)
    
    #! simplification
    #// # first we update total_tank_stock that can 1) take delta_total_tank_stock or 2) be unchanged
    #// data = update_total_tank_stock_for_second_crop_cycle(j, data)# verif ok
    #// # # then previous_total_tank_stock can 1) take 0 or 2) be unchanged
    #// data = update_previous_total_tank_stock_for_second_crop_cycle(j, data)
    #// # # delta_total_tank_stock can 1) be incremented of previous_total_tank_stock or 2) be unchanged
    #//data = update_delta_total_tank_stock_step_2(j, data)
    
    #// # # here, in case 1, In this function, if the variation of transpirable water
    #// # (delta_total_tank_stock) increases above the depth of humectation front
    #// # (hum), if the depth of humectation front (hum) is above the
    #// # previous_root_tank_capacity (condition 1 passed, and 2 failed,
    #// # which should be the case for most of the simulations that will be
    #// # single-season), and if the depth of humectation front (hum) has decreased
    #// # since the previous day (condition 3 passed), then total_tank_stock takes the value of 
    #// # delta_total_tank_stock, previous_total_tank_stock equals 0, and 
    #// # delta_total_tank_stock is incremented by previous_total_tank_stock.
    #// # 
    #// # in case 2, nothing happens.


    # Updates the water height to humectation front (humectation_front, mm) by
    # bounding it between delta_total_tank_stock and total_tank_capacity, so
    # that humectation front cannot go down indefinitely.
    data = apply_humectation_front_boundaries(j, data)

    # computes drainage
    data = compute_drainage(j, data)
   
    # Updates the height of water in the tank of water accessible to roots
    # ("root_tank_stock", mm), so that the transpirable water added to the root
    # tank stock for the day cannot be higher than both the root tank capacity,
    # and the total tank stock.
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