import numpy as np
import copy
import xarray as xr


def _to_numpy(values):
    if hasattr(values, "values"):
        return np.asarray(values.values)
    return np.asarray(values)


def reset(j, data):

  data = data.copy(deep=True)

  # when reaching stage 7, we reset the main phenological variables to zero
  data["changePhase"][j:,:,:] = np.where(data["numPhase"][j,:,:] == 7, 0, data["changePhase"][j,:,:])#[np.newaxis,...]
  data["sdj"][j:,:,:] = np.where(data["numPhase"][j,:,:] == 7, 0, data["sdj"][j,:,:])#[np.newaxis,...]
  data["ruRac"][j:,:,:] = np.where(data["numPhase"][j,:,:] == 7, 0, data["numPhase"][j,:,:])#[np.newaxis,...]
  data["nbJourCompte"][j:,:,:] = np.where(data["numPhase"][j,:,:] == 7, 0, data["numPhase"][j,:,:])#[np.newaxis,...]
  data["startLock"][j:,:,:] = np.where(data["numPhase"][j,:,:] == 7, 1, data["startLock"][j,:,:])#[np.newaxis,...]
  # and we leave numPhas last
  data["numPhase"][j:,:,:] = np.where(data["numPhase"][j,:,:] == 7, 0, data["numPhase"][j,:,:])#[np.newaxis,...]

  return data


def testing_for_initialization(j, data, paramITK, paramVariete):
    """Initialize the crop when sowing conditions are met.

    Role in SARRA-Py
    ----------------
    Handles the transition from phase 0, no active crop, to phase 1, crop
    initiation after sowing conditions become favorable.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset
        Simulation state. Daily variables are expected on the same raster
        dimensions as ``rain``, usually ``("time", "x", "y")``.
    paramITK : dict
        Management parameters. Reads ``seuilEauSemis`` in mm.
    paramVariete : dict
        Variety parameters. Reads ``SDJLevee`` in degree-days.

    Reads
    -----
    data["numPhase"], data["sowing_date"], data["surface_tank_stock"]
        Current phase, sowing date as a relative day index, and surface water
        stock in mm.

    Writes
    ------
    data["numPhase"], data["changePhase"], data["seuilTempPhaseSuivante"],
    data["initPhase"]
        ``numPhase`` and ``seuilTempPhaseSuivante`` are broadcast from ``j`` to
        the end of the simulation. ``changePhase`` and ``initPhase`` are set on
        the current day.

    Returns
    -------
    xarray.Dataset
        The same dataset, mutated in place.

    Assumptions
    -----------
    Initialization occurs where ``numPhase == 0``, ``j >= sowing_date`` and
    ``surface_tank_stock >= seuilEauSemis``. ``initPhase`` prevents an immediate
    second phase increment on the same day.
    """

    #! replacing stRuSurf by surface_tank_stock
    condition = \
        (data["numPhase"][j, :, :] == 0) & \
        (j >= data["sowing_date"][j,:,:]) & \
        (data["surface_tank_stock"][j, :, :] >= paramITK["seuilEauSemis"])
        # & (data["startLock"][j,:,:] == 0)

    data["numPhase"][j:, :, :] = xr.where(
        condition, 1, data["numPhase"][j, :, :])

    data["changePhase"][j, :, :] = xr.where(
        condition, 1, data["changePhase"][j, :, :])

    data["seuilTempPhaseSuivante"][j:, :, :] = xr.where(
        condition,
        paramVariete["SDJLevee"],
        data["seuilTempPhaseSuivante"][j, :, :],
    )

    #flagging phase change has been done
    data["initPhase"][j, :, :] = xr.where(
        condition,
        1,
        data["initPhase"][j, :, :]
    )

    return data



def flag_change_phase(j, data, num_phase):
    """Flag a thermal-time phase transition on the current day.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset
        Simulation state with daily raster variables on rainfall-like
        dimensions.
    num_phase : int
        Phase number to test.

    Reads
    -----
    data["numPhase"], data["sdj"], data["seuilTempPhaseSuivante"]
        Current phenological phase, accumulated thermal time, and thermal-time
        threshold for the next phase. Thermal-time variables are expected in
        degree-days.

    Writes
    ------
    data["changePhase"]
        Sets ``changePhase[j, :, :]`` to 1 where ``numPhase == num_phase`` and
        ``sdj >= seuilTempPhaseSuivante``.

    Returns
    -------
    xarray.Dataset
        The same dataset, mutated in place.
    """
    # flagging the day for phase change
    condition = \
        (data["numPhase"][j,:,:] == num_phase) & \
        (data["sdj"][j,:,:] >= data["seuilTempPhaseSuivante"][j,:,:])

    data["changePhase"][j,:,:] = xr.where(
        condition,
        1,
        data["changePhase"][j,:,:],
    )

    return data


def update_thermal_time_next_phase(j, data, num_phase, thermal_time_threshold):
    """Update the accumulated threshold for the next phenological phase.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset
        Simulation state with daily raster variables.
    num_phase : int
        Phase number for which the transition is being handled.
    thermal_time_threshold : float
        Phase-specific thermal-time increment in degree-days.

    Reads
    -----
    data["numPhase"], data["changePhase"], data["seuilTempPhaseSuivante"]

    Writes
    ------
    data["seuilTempPhaseSuivante"]
        Broadcasts the updated threshold from ``j`` onward where
        ``numPhase == num_phase`` and ``changePhase == 1``.

    Returns
    -------
    xarray.Dataset
        The same dataset, mutated in place.

    Notes
    -----
    The caller supplies the phase-specific increment, for example ``SDJLevee``,
    ``SDJBVP``, ``SDJRPR``, ``SDJMatu1`` or ``SDJMatu2``.
    """
    condition = \
        (data["numPhase"][j,:,:] == num_phase) & \
        (data["changePhase"][j,:,:] == 1)

    data["seuilTempPhaseSuivante"][j:,:,:] = np.where(
        condition,
        data["seuilTempPhaseSuivante"][j,:,:] + thermal_time_threshold,
        data["seuilTempPhaseSuivante"][j,:,:]
    )  

    return data





def increment_phase_number(j, data):
    """Increment the phenological phase after a transition has been flagged.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset
        Simulation state with daily raster variables.

    Reads
    -----
    data["numPhase"], data["changePhase"], data["initPhase"]

    Writes
    ------
    data["numPhase"], data["initPhase"]
        Broadcasts ``numPhase + 1`` from ``j`` onward where the current phase
        is non-zero, ``changePhase == 1`` and ``initPhase != 1``. Sets
        ``initPhase[j, :, :]`` to 1 at the same pixels.

    Returns
    -------
    xarray.Dataset
        The same dataset, mutated in place.

    Assumptions
    -----------
    ``initPhase`` acts as a same-day guard so a pixel does not move through two
    phases during one phenology evaluation.
    """

    condition = \
        (data["numPhase"][j,:,:] != 0) & \
        (data["changePhase"][j,:,:] == 1) & \
        (data["initPhase"][j,:,:] != 1)  

    # incrementing phase number
    data["numPhase"][j:,:,:] = np.where(
        condition,
        data["numPhase"][j,:,:] + 1 ,
        data["numPhase"][j,:,:],
    )

    # flagging this day as having been incremented
    data["initPhase"][j, :, :] = xr.where(
        condition,
        1,
        data["initPhase"][j, :, :]
    ) 
    return data





def update_thermal_time_previous_phase(j, data, num_phase):
    """Store the current thermal-time threshold as the previous phase threshold.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset
        Simulation state with daily raster variables.
    num_phase : int
        Phase number whose transition is being handled.

    Reads
    -----
    data["numPhase"], data["changePhase"], data["seuilTempPhaseSuivante"]

    Writes
    ------
    data["seuilTempPhasePrec"]
        Broadcasts the current ``seuilTempPhaseSuivante`` from ``j`` onward
        where ``numPhase == num_phase`` and ``changePhase == 1``.

    Returns
    -------
    xarray.Dataset
        The same dataset, mutated in place.

    Units
    -----
    ``seuilTempPhasePrec`` and ``seuilTempPhaseSuivante`` are expected in
    degree-days.
    """
    condition = \
        (data["numPhase"][j,:,:] == num_phase) & \
        (data["changePhase"][j,:,:] == 1)

    data["seuilTempPhasePrec"][j:,:,:] = xr.where(
        condition,
        data["seuilTempPhaseSuivante"][j,:,:],
        data["seuilTempPhasePrec"][j,:,:]
    )
    return data
    




def update_pheno_phase_1_to_2(j, data, paramVariete):
    """Handle the phase 1 to phase 2 thermal-time transition.

    Role in SARRA-Py
    ----------------
    Applies the generic transition sequence for the end of phase 1: flag the
    transition day, update the next thermal-time threshold, then increment the
    phase number.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset
        Simulation state with rainfall-like daily dimensions.
    paramVariete : dict
        Reads ``SDJLevee`` in degree-days.

    Reads
    -----
    data["numPhase"], data["sdj"], data["seuilTempPhaseSuivante"],
    data["changePhase"], data["initPhase"]

    Writes
    ------
    data["changePhase"], data["seuilTempPhaseSuivante"], data["numPhase"],
    data["initPhase"]

    Returns
    -------
    xarray.Dataset
        The same dataset, mutated in place.
    """

    num_phase = 1
    thermal_time_threshold = paramVariete["SDJLevee"]

    # flagging the day for phase change
    data = flag_change_phase(j, data, num_phase)

    # updating thermal time to next phase 
    data = update_thermal_time_next_phase(j, data, num_phase, thermal_time_threshold)

    # updating phase number and flagging incrementation
    data = increment_phase_number(j, data)   
    
    return data





def update_pheno_phase_2_to_3(j, data, paramVariete):
    """Handle the phase 2 to phase 3 thermal-time transition.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset
        Simulation state with rainfall-like daily dimensions.
    paramVariete : dict
        Reads ``SDJBVP`` in degree-days.

    Reads
    -----
    data["numPhase"], data["sdj"], data["seuilTempPhaseSuivante"],
    data["changePhase"], data["initPhase"]

    Writes
    ------
    data["changePhase"], data["seuilTempPhasePrec"],
    data["seuilTempPhaseSuivante"], data["numPhase"], data["initPhase"]

    Returns
    -------
    xarray.Dataset
        The same dataset, mutated in place.

    Notes
    -----
    Unlike phase 1 to 2, this transition stores the previous threshold in
    ``seuilTempPhasePrec`` for later phase-specific calculations.
    """

    num_phase = 2
    thermal_time_threshold = paramVariete["SDJBVP"]

    # flagging the day for phase change
    data = flag_change_phase(j, data, num_phase)

    # saving "previous thermal time to next phase" to be used 
    data = update_thermal_time_previous_phase(j, data, num_phase)

    # updating thermal time to next phase 
    data = update_thermal_time_next_phase(j, data, num_phase, thermal_time_threshold)

    # updating phase number and flagging incrementation
    data = increment_phase_number(j, data)  

    return data    



def update_pheno_phase_3_to_4(j, data):
    """Handle the phase 3 to phase 4 photoperiodic transition.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset
        Simulation state with rainfall-like daily dimensions.

    Reads
    -----
    data["numPhase"], data["phasePhotoper"], data["changePhase"],
    data["initPhase"]

    Writes
    ------
    data["changePhase"], data["phasePhotoper"], data["numPhase"],
    data["initPhase"]

    Returns
    -------
    xarray.Dataset
        The same dataset, mutated in place.

    Assumptions
    -----------
    Phase 3 ends when ``phasePhotoper[j, :, :] == 0``. The value of
    ``phasePhotoper`` is updated elsewhere by ``update_photoperiodism``.
    """

    # flagging the day for phase change (specific to phase 3)
    condition = \
        (data["numPhase"][j,:,:] == 3) & \
        (data["phasePhotoper"][j,:,:] == 0)

    data["changePhase"][j,:,:] = xr.where(
        condition,
        1,
        data["changePhase"][j,:,:],
    )

    # updating phasePhotoper (specific to phase 3)
    condition = \
        (data["numPhase"][j,:,:] == 3) & \
        (data["changePhase"][j,:,:] == 1)

    data["phasePhotoper"][j,:,:] = np.where(
        condition,
        1,
        data["phasePhotoper"][j,:,:],
    )  

    # updating phase number and flagging incrementation
    data = increment_phase_number(j, data)   

    return data







def update_pheno_phase_4_to_5(j, data, paramVariete):
    """Handle the phase 4 to phase 5 thermal-time transition.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset
        Simulation state with rainfall-like daily dimensions.
    paramVariete : dict
        Reads ``SDJRPR`` in degree-days.

    Reads
    -----
    data["numPhase"], data["sdj"], data["seuilTempPhaseSuivante"],
    data["changePhase"], data["initPhase"]

    Writes
    ------
    data["changePhase"], data["seuilTempPhasePrec"],
    data["seuilTempPhaseSuivante"], data["numPhase"], data["initPhase"]

    Returns
    -------
    xarray.Dataset
        The same dataset, mutated in place.
    """

    num_phase = 4
    thermal_time_threshold = paramVariete["SDJRPR"]

    # flagging the day for phase change
    data = flag_change_phase(j, data, num_phase)

    # saving "previous thermal time to next phase" to be used 
    data = update_thermal_time_previous_phase(j, data, num_phase)

    # updating thermal time to next phase 
    data = update_thermal_time_next_phase(j, data, num_phase, thermal_time_threshold)

    # updating phase number and flagging incrementation
    data = increment_phase_number(j, data)  

    return data 








def update_pheno_phase_5_to_6(j, data, paramVariete):
    """Handle the phase 5 to phase 6 thermal-time transition.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset
        Simulation state with rainfall-like daily dimensions.
    paramVariete : dict
        Reads ``SDJMatu1`` in degree-days.

    Reads
    -----
    data["numPhase"], data["sdj"], data["seuilTempPhaseSuivante"],
    data["changePhase"], data["initPhase"]

    Writes
    ------
    data["changePhase"], data["seuilTempPhasePrec"],
    data["seuilTempPhaseSuivante"], data["numPhase"], data["initPhase"]

    Returns
    -------
    xarray.Dataset
        The same dataset, mutated in place.
    """

    num_phase = 5
    thermal_time_threshold = paramVariete["SDJMatu1"]

    # flagging the day for phase change
    data = flag_change_phase(j, data, num_phase)

    # saving "previous thermal time to next phase" to be used 
    data = update_thermal_time_previous_phase(j, data, num_phase)

    # updating thermal time to next phase 
    data = update_thermal_time_next_phase(j, data, num_phase, thermal_time_threshold)

    # updating phase number and flagging incrementation
    data = increment_phase_number(j, data)  

    return data 






def update_pheno_phase_6_to_7(j, data, paramVariete):
    """Handle the phase 6 to phase 7 thermal-time transition.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset
        Simulation state with rainfall-like daily dimensions.
    paramVariete : dict
        Reads ``SDJMatu2`` in degree-days.

    Reads
    -----
    data["numPhase"], data["sdj"], data["seuilTempPhaseSuivante"],
    data["changePhase"], data["initPhase"]

    Writes
    ------
    data["changePhase"], data["seuilTempPhasePrec"],
    data["seuilTempPhaseSuivante"], data["numPhase"], data["initPhase"]

    Returns
    -------
    xarray.Dataset
        The same dataset, mutated in place.
    """

    num_phase = 6
    thermal_time_threshold = paramVariete["SDJMatu2"]

    # flagging the day for phase change
    data = flag_change_phase(j, data, num_phase)

    # saving "previous thermal time to next phase" to be used 
    data = update_thermal_time_previous_phase(j, data, num_phase)

    # updating thermal time to next phase 
    data = update_thermal_time_next_phase(j, data, num_phase, thermal_time_threshold)

    # updating phase number and flagging incrementation
    data = increment_phase_number(j, data)  

    return data 






def EvalPhenoSarrahV3(j, data, paramITK, paramVariete): 
    """Evaluate phenological phase transitions for one simulation day.

    Role in SARRA-Py
    ----------------
    Coordinates the daily phenology update. It tests crop initialization and
    then applies the phase-specific transition helpers for phases 1 through 7.
    It is called near the beginning of the daily model loop.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset
        Simulation state. Phenology variables are expected on rainfall-like
        daily raster dimensions, usually ``("time", "x", "y")``.
    paramITK : dict
        Management parameters. Reads ``seuilEauSemis`` in mm through
        ``testing_for_initialization``.
    paramVariete : dict
        Variety parameters. Reads thermal-time thresholds ``SDJLevee``,
        ``SDJBVP``, ``SDJRPR``, ``SDJMatu1`` and ``SDJMatu2`` in degree-days.

    Reads
    -----
    data["numPhase"], data["sowing_date"], data["surface_tank_stock"],
    data["sdj"], data["seuilTempPhaseSuivante"], data["seuilTempPhasePrec"],
    data["changePhase"], data["initPhase"], data["phasePhotoper"]

    Writes
    ------
    data["numPhase"], data["changePhase"], data["initPhase"],
    data["seuilTempPhaseSuivante"], data["seuilTempPhasePrec"],
    data["phasePhotoper"]

    Returns
    -------
    xarray.Dataset
        The same dataset, mutated in place.

    Phenological phases
    -------------------
    The code uses phase numbers 0 to 7: 0 no active crop, 1 crop initiation to
    emergence, 2 emergence to photoperiod-sensitive phase, 3 photoperiodic
    phase, 4 reproductive phase, 5 early maturation, 6 late maturation, and
    7 harvest day.

    Assumptions
    -----------
    Thermal transitions occur when ``sdj >= seuilTempPhaseSuivante``. The end
    of phase 3 is controlled by ``phasePhotoper``. Transition helpers broadcast
    some state variables from ``j`` onward, so loop order is part of the model
    behavior.

    References
    ----------
    Translated from the ``EvalPhenoSarrahV3`` procedure of the SARRA-H Pascal
    code (``phenologie.pas`` and ``exmodules.pas``), as noted in the original
    source comments.
    """

    # in order to save computational resources, we test if there is
    # the time step contains any pixel with the considered phases
    # before testing for initialization or updating the phenological phases

    data = testing_for_initialization(j, data, paramITK, paramVariete)
    data = update_pheno_phase_1_to_2(j, data, paramVariete)
    data = update_pheno_phase_2_to_3(j, data, paramVariete)
    data = update_pheno_phase_3_to_4(j, data)
    data = update_pheno_phase_4_to_5(j, data, paramVariete)
    data = update_pheno_phase_5_to_6(j, data, paramVariete)
    data = update_pheno_phase_6_to_7(j, data, paramVariete)

    return data






def calculate_daily_thermal_time(j, data, paramVariete):
    """Compute daily thermal time for one simulation day.

    Role in SARRA-Py
    ----------------
    Fills ``data["ddj"][j, :, :]`` for daily model variants that compute
    thermal time inside the loop.

    Equation
    --------
    The active implementation uses mean daily temperature only. For
    ``T = tpMoy[j, :, :]``:

    ``ddj = max(min(TOpt1, T), TBase) - TBase`` if ``T <= TOpt2``.

    Otherwise:

    ``ddj = (TOpt1 - TBase) * (1 - (min(TLim, T) - TOpt2) /
    (TLim - TOpt2))``.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset or dict[str, numpy.ndarray]
        Simulation state. Reads ``tpMoy`` and writes ``ddj`` with matching daily
        raster dimensions.
    paramVariete : dict
        Reads ``TBase``, ``TOpt1``, ``TOpt2`` and ``TLim`` in degrees C.

    Reads
    -----
    data["tpMoy"]
        Mean daily temperature in degrees C.

    Writes
    ------
    data["ddj"]
        Daily thermal time in degree-days for the current day.

    Returns
    -------
    xarray.Dataset or dict[str, numpy.ndarray]
        The same model state, mutated in place.

    Notes
    -----
    Historical comments mention a more detailed ``TMin``/``TMax`` formulation.
    This docstring documents the active ``tpMoy`` implementation only; changing
    to a ``TMin``/``TMax`` equation would be a scientific change requiring
    validation.
    """

    tp_moy = _to_numpy(data["tpMoy"][j,:,:])

    data["ddj"][j,:,:] = np.where(
        tp_moy <= paramVariete["TOpt2"],
        np.maximum(np.minimum(paramVariete["TOpt1"], tp_moy), paramVariete["TBase"]) - paramVariete["TBase"],
        (paramVariete["TOpt1"] - paramVariete["TBase"]) * (1 - ((np.minimum(paramVariete["TLim"], tp_moy) - paramVariete["TOpt2"]) / (paramVariete["TLim"] - paramVariete["TOpt2"]))),
    ) 

    return data





def calculate_once_daily_thermal_time(data, paramVariete):
    """Compute daily thermal time for the full simulation period.

    Role in SARRA-Py
    ----------------
    Vectorized notebook helper that fills ``data["ddj"]`` before calling
    ``run_model``. It uses the same active equation as
    ``calculate_daily_thermal_time`` when ``tpMoy`` is available for the whole
    period.

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
        Simulation state. Reads ``tpMoy`` and writes ``ddj`` with matching
        dimensions, usually ``("time", "x", "y")`` for xarray inputs.
    paramVariete : dict
        Reads ``TBase``, ``TOpt1``, ``TOpt2`` and ``TLim`` in degrees C.

    Reads
    -----
    data["tpMoy"]
        Mean daily temperature in degrees C.

    Writes
    ------
    data["ddj"]
        Daily thermal time in degree-days for all time steps.

    Returns
    -------
    xarray.Dataset or dict[str, numpy.ndarray]
        The same model state, mutated in place.

    Notes
    -----
    Historical comments mention a more detailed ``TMin``/``TMax`` formulation.
    This docstring documents the active ``tpMoy`` implementation only; changing
    to a ``TMin``/``TMax`` equation would be a scientific change requiring
    validation.
    """

    tp_moy = _to_numpy(data["tpMoy"])
    ddj = np.where(
        tp_moy <= paramVariete["TOpt2"],
        np.maximum(np.minimum(paramVariete["TOpt1"], tp_moy), paramVariete["TBase"]) - paramVariete["TBase"],
        (paramVariete["TOpt1"] - paramVariete["TBase"]) * (1 - ((np.minimum(paramVariete["TLim"], tp_moy) - paramVariete["TOpt2"]) / (paramVariete["TLim"] - paramVariete["TOpt2"]))),
    ) 

    if hasattr(data["ddj"], "values"):
        data["ddj"].data = ddj
    else:
        data["ddj"][:] = ddj

    return data






def calculate_sum_of_thermal_time(j, data):
    """Accumulate thermal time since crop initialization.

    Role in SARRA-Py
    ----------------
    Updates ``sdj``, the accumulated degree-day sum used by phenological phase
    transitions.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset or dict[str, numpy.ndarray]
        Simulation state with daily raster variables.

    Reads
    -----
    data["sowing_date"], data["numPhase"], data["sdj"], data["ddj"]
        ``sowing_date`` is a relative day index. ``ddj`` and ``sdj`` are in
        degree-days.

    Writes
    ------
    data["sdj"]
        Broadcasts from ``j`` onward. Where ``j >= sowing_date`` and
        ``numPhase >= 1``, writes ``sdj[j - 1] + ddj[j]``; otherwise writes 0.

    Returns
    -------
    xarray.Dataset or dict[str, numpy.ndarray]
        The same model state, mutated in place.

    Notes
    -----
    The active code does not special-case ``j == 0`` and therefore reads
    ``sdj[j - 1]``. Historical comments indicate that SARRA-H stops
    accumulation when ``numPhase > 7``; that behavior is not implemented here.
    """
    data["sdj"][j:,:,:] = xr.where(
        (j >= data["sowing_date"][j,:,:]) & (data["numPhase"][j,:,:] >= 1),
        data["sdj"][j-1,:,:] + data["ddj"][j,:,:],
        0,
    )
    return data





def update_root_growth_speed(j, data, paramVariete):
    """Update root growth speed according to the current phenological phase.

    Role in SARRA-Py
    ----------------
    Sets ``vRac``, the reference daily root growth speed, used later by water
    balance functions that update the root-zone reservoir.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset or dict[str, numpy.ndarray]
        Simulation state with daily raster variables.
    paramVariete : dict
        Reads phase-specific root growth speeds ``VRacLevee``, ``VRacBVP``,
        ``VRacPSP``, ``VRacRPR``, ``VRacMatu1`` and ``VRacMatu2`` in mm/day.

    Reads
    -----
    data["numPhase"], data["vRac"]

    Writes
    ------
    data["vRac"]
        Broadcasts the selected root growth speed from ``j`` onward. Active
        crop phases use phase-specific values; phases 0 and 7 are set to 0.

    Returns
    -------
    xarray.Dataset or dict[str, numpy.ndarray]
        The same model state, mutated in place.

    Notes
    -----
    The active loop applies explicit updates for phases 1 through 5. A mapping
    for phase 6 exists in the code, but ``range(1, 6)`` does not iterate over
    phase 6. This docstring records the current implementation without changing
    it; whether phase 6 should receive ``VRacMatu2`` requires scientific
    validation.

    References
    ----------
    Adapted from the ``EvalVitesseRacSarraV3`` procedure of the SARRA-H Pascal
    code (``phenologie.pas`` and ``exmodules 1 & 2.pas``), as noted in the
    original source comments.
    """


    phase_correspondances = {
        1: paramVariete['VRacLevee'],
        2: paramVariete['VRacBVP'],
        3: paramVariete['VRacPSP'],
        4: paramVariete['VRacRPR'],
        5: paramVariete['VRacMatu1'],
        6: paramVariete['VRacMatu2'],
    }

    # phases 1 to 6 
    for phase in range(1,6):
        data["vRac"][j:,:,:] = np.where(
            data["numPhase"][j,:,:] == phase,
            phase_correspondances[phase],
            data["vRac"][j,:,:],
        )

    # phases 0 or 7
    data["vRac"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 0) | (data["numPhase"][j,:,:] == 7),
        0,
        data["vRac"][j,:,:],
    )

    return data




def update_photoperiodism(j, data, paramVariete):
    """Update photoperiodic response variables during phase 3.

    Role in SARRA-Py
    ----------------
    Computes the daily ``sumPP`` indicator and updates ``phasePhotoper``. The
    following phenology evaluation uses ``phasePhotoper == 0`` to end phase 3.

    Equation
    --------
    The active implementation computes:

    ``thermal_time_since_previous_phase = max(0.01, sdj - seuilTempPhasePrec)``

    ``time_above_critical_day_length = max(0, dureeDuJour - PPCrit)``

    If ``numPhase == 3`` and ``changePhase == 1``, ``sumPP`` is set to 100.
    Otherwise, while ``numPhase == 3``:

    ``sumPP = (1000 / thermal_time_since_previous_phase) ** PPExp
    * time_above_critical_day_length / (SeuilPP - PPCrit)``

    Finally, ``phasePhotoper`` is set to 0 from ``j`` onward where
    ``numPhase == 3`` and ``sumPP < PPsens``.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset or dict[str, numpy.ndarray]
        Simulation state with daily raster variables.
    paramVariete : dict
        Reads ``PPExp``, ``PPCrit``, ``SeuilPP`` and ``PPsens``. Day-length
        parameters are expected in hours where applicable.

    Reads
    -----
    data["sdj"], data["seuilTempPhasePrec"], data["dureeDuJour"],
    data["numPhase"], data["changePhase"], data["sumPP"],
    data["phasePhotoper"]
        ``sdj`` and ``seuilTempPhasePrec`` are in degree-days.
        ``dureeDuJour`` is in hours.

    Writes
    ------
    data["sumPP"], data["phasePhotoper"]
        ``sumPP`` is written on the current day. ``phasePhotoper`` is
        broadcast from ``j`` onward.

    Returns
    -------
    xarray.Dataset or dict[str, numpy.ndarray]
        The same model state, mutated in place.

    Notes
    -----
    The audit identifies this as an "Impatience"-style photoperiodic response.
    The exact calibration and validity of ``PPExp``, ``PPsens``, ``PPCrit`` and
    ``SeuilPP`` should remain under scientific validation. ``SeuilPP == PPCrit``
    would make the active equation divide by zero.

    References
    ----------
    The audit notes Dingkuhn et al. (2008) for the photoperiodic "Impatience"
    model, and the source comments note adaptation from ``PhotoperSarrahV3`` in
    the SARRA-H Pascal code.
    """

    thermal_time_since_previous_phase = np.maximum(0.01, data["sdj"][j,:,:] - data["seuilTempPhasePrec"][j,:,:])
    time_above_critical_day_length = np.maximum(0, data["dureeDuJour"][j,:,:] - paramVariete["PPCrit"])

    data["sumPP"][j,:,:] = np.where(
        data["numPhase"][j,:,:] == 3,
        np.where(
            data["changePhase"][j,:,:] == 1,
            # if numPhase = 3 and changePhase == 1, sumPP = 100
            100,
            # if numPhase = 3 and changePhase != 1, sumPP calculated through formula
            ((1000 / thermal_time_since_previous_phase) ** (paramVariete["PPExp"])) \
                * time_above_critical_day_length / (paramVariete["SeuilPP"] - paramVariete["PPCrit"]),
        ),
        # if numPhase != 3, sumPP is not updated
        data["sumPP"][j,:,:],
    )

    data["phasePhotoper"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 3) & (data["sumPP"][j,:,:] < paramVariete["PPsens"]),
        0,
        data["phasePhotoper"][j,:,:],
    )

    return data




def MortaliteSarraV3(j, data, paramITK, paramVariete):
    """Apply the juvenile mortality rule for stressed young plants.

    Role in SARRA-Py
    ----------------
    Tracks days since emergence and counts early stress days. When the stress
    counter reaches the configured mortality threshold, the current pixel is
    reset to no active crop for selected variables.

    Parameters
    ----------
    j : int
        Current daily time index.
    data : xarray.Dataset or dict[str, numpy.ndarray]
        Simulation state with daily raster variables.
    paramITK : dict
        Reads ``nbjTestSemis``, the number of days after emergence during which
        juvenile stress is counted.
    paramVariete : dict
        Reads ``seuilCstrMortality``, the stress-day threshold.

    Reads
    -----
    data["numPhase"], data["changePhase"], data["nbJourCompte"],
    data["nbjStress"], data["deltaBiomasseAerienne"],
    data["root_tank_capacity"]
        ``deltaBiomasseAerienne`` is expected in kg/(ha.day).
        ``root_tank_capacity`` is expected in mm.

    Writes
    ------
    data["nbJourCompte"], data["nbjStress"], data["numPhase"],
    data["root_tank_capacity"]
        ``nbJourCompte`` and ``nbjStress`` are reset at emergence, then updated
        from ``j`` onward. When mortality triggers, ``numPhase[j, :, :]`` and
        ``root_tank_capacity[j, :, :]`` are set to 0, and ``nbjStress`` is reset
        from ``j`` onward.

    Returns
    -------
    xarray.Dataset or dict[str, numpy.ndarray]
        The same model state, mutated in place.

    Notes
    -----
    The active mortality trigger is ``nbjStress == seuilCstrMortality``. The
    audit flags this equality test as a point requiring validation because it is
    not ``>=``. This docstring records the current behavior without changing it.

    References
    ----------
    Adapted from the ``MortaliteSarraV3`` procedure of the SARRA-H Pascal code
    (``bilancarbonsarra.pas`` and ``exmodules 1 & 2.pas``), as noted in the
    original source comments.
    """

    condition = (data["numPhase"][j,:,:] >= 2) & \
        (data["numPhase"][j,:,:] == 2) & \
        (data["changePhase"][j,:,:] == 1)

    data['nbJourCompte'][j:,:,:] = np.where(
        condition,
        0,
        data['nbJourCompte'][j,:,:],
    )

    data['nbjStress'][j:,:,:] = np.where(
        condition,
        0,
        data['nbjStress'][j,:,:],
    )


    condition = (data["numPhase"][j,:,:] >= 2)

    data['nbJourCompte'][j:,:,:] = np.where(
        condition,
        data['nbJourCompte'][j,:,:] + 1,
        data['nbJourCompte'][j,:,:],
    )


    condition = (data["numPhase"][j,:,:] >= 2) & \
        (data["nbJourCompte"][j,:,:] < paramITK["nbjTestSemis"]) & \
        (data["deltaBiomasseAerienne"][j,:,:] < 0)

    data["nbjStress"][j:,:,:] = np.where(
        condition,
        data["nbjStress"][j,:,:] + 1,
        data["nbjStress"][j,:,:],                           
    )


    condition = (data["numPhase"][j,:,:] >= 2) & \
        (data["nbjStress"][j,:,:] == paramVariete["seuilCstrMortality"])

    data["numPhase"][j,:,:] = np.where(
        condition,
        0,
        data["numPhase"][j,:,:],
    )

    #! renaming stRurMax with root_tank_capacity
    #// data["stRurMax"][j,:,:] = np.where(
    data["root_tank_capacity"][j,:,:] = np.where(
        condition,
        0,
        #// data["stRurMax"][j,:,:],
        data["root_tank_capacity"][j,:,:],
    )

    data["nbjStress"][j:,:,:] = np.where(
        condition,
        0,
        data["nbjStress"][j,:,:],
    )

    return data
