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

    Phase 0 becomes phase 1 when the date is at or after sowing and surface
    water exceeds `seuilEauSemis` (mm). `SDJLevee` initializes the next
    degree-day threshold; `initPhase` prevents a second phase change that day.
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

    Sets `changePhase` where the current phase matches `num_phase` and
    accumulated degree-days reach `seuilTempPhaseSuivante`.
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

    Adds the phase-specific degree-day threshold and propagates it from day
    `j` onward where `changePhase == 1`.
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

    `initPhase` acts as a same-day guard so a pixel cannot move through two
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

    Used by later phase-specific calculations; thresholds are in degree-days.
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

    Uses `SDJLevee` as the degree-day increment for the next threshold.
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

    Stores the previous threshold, then adds `SDJBVP` degree-days for the next
    phase boundary.
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

    Stores the previous threshold, then adds `SDJRPR` degree-days for the next
    phase boundary.
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

    Stores the previous threshold, then adds `SDJMatu1` degree-days for the
    next phase boundary.
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

    Stores the previous threshold, then adds `SDJMatu2` degree-days to reach
    harvest phase 7.
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

    Phases 0-7 represent no crop, initiation, vegetative development,
    photoperiod-sensitive phase, reproductive phase, two maturation steps and
    harvest. Thermal transitions use accumulated degree-days; phase 3 ends via
    `phasePhotoper`.

    Source status: code-observed SARRA-Py sequence, source-related to SARRA-H
    procedure names and phase structure.
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

    The active implementation uses mean daily temperature `T = tpMoy[j]`:

    ``ddj = max(min(TOpt1, T), TBase) - TBase`` if ``T <= TOpt2``.

    Otherwise it decreases linearly from `TOpt2` to `TLim`. Temperatures are in
    degrees C and `ddj` is in degree-days. Historical Tmin/Tmax comments remain
    a validation question, not active code.

    Source status: code-observed.
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

    Vectorized notebook helper using the same active `tpMoy` equation as
    `calculate_daily_thermal_time`:

    ``ddj = max(min(TOpt1, T), TBase) - TBase`` if ``T <= TOpt2``.

    Otherwise it decreases linearly from `TOpt2` to `TLim`. Temperatures are in
    degrees C and `ddj` is in degree-days.

    Source status: code-observed.
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

    `sdj` is updated from `sdj[j - 1] + ddj[j]` where the crop has been sown
    and `numPhase >= 1`; otherwise it is reset to 0.

    Source status: code-observed.
    """
    data["sdj"][j:,:,:] = xr.where(
        (j >= data["sowing_date"][j,:,:]) & (data["numPhase"][j,:,:] >= 1),
        data["sdj"][j-1,:,:] + data["ddj"][j,:,:],
        0,
    )
    return data





def update_root_growth_speed(j, data, paramVariete):
    """Update root growth speed according to the current phenological phase.

    Uses phase-specific `VRac*` parameters in mm/day. The active loop updates
    phases 1-5; the phase-6 mapping exists but is not iterated.

    Source status: code-observed, source-related to SARRA-H root-growth
    procedure comments.
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

    During phase 3, `sumPP` is reset to 100 on phase entry; otherwise:

    ``sumPP = (1000 / thermal_time_since_previous_phase) ** PPExp
    * time_above_critical_day_length / (SeuilPP - PPCrit)``

    `phasePhotoper` becomes 0 when `sumPP < PPsens`. This is related to
    "Impatience"-style photoperiodism, but exact calibration remains a
    validation question.

    Source status: source-related; not an exact Impatience implementation claim.
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

    Counts early days with non-positive aerial biomass increment. Mortality
    triggers when `nbjStress == seuilCstrMortality`, which is an active-code
    detail still listed for scientific validation.

    Source status: code-observed, source-related to legacy SARRA-H procedure
    comments.
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
