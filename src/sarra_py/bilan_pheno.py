import numpy as np
import copy
import xarray as xr

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
    """
    This function tests if the conditions are met to initiate the crop.

    If numPhase is 0, if the current day is equal or above the sowing date, and
    if surface_tank_stock is above the threshold for sowing, we initiate the
    crop :

    1) we set numPhase to 1 ; we broadcast the value over remaining days.
    2) we set changePhase of this particular day to 1.
    3) set the sum of thermal time to the next phase (seuilTempPhaseSuivante) to
       be SDJLevee ; we broadcast the value over remaining days.
    4) we set initPhase to 1 ; we broadcast the value over remaining days.

    initPhase is only used in update_pheno_phase_1_to_2 function, so that we do
    not go directly from phase 0 to phase 2. It is used as a specific flag for
    phase 0 to 1 transition.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramITK (_type_): _description_

    Returns:
        _type_: _description_
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
    """
    This function flags the day for phase change.

    If the phase number is above the num_phase value, and if the sum of thermal
    time is above the threshold, this function returns changePhase flags.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        num_phase (_type_): _description_

    Returns:
        _type_: _description_
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
    """
    This function updates the sum of thermal time needed to reach the next
    phase.

    When numPhase equals the requested phase number, and if changePhase is 1
    (meaning that we are at a phase transition day), the seuilTempPhaseSuivante
    is incremented by the thermal_time_threshold value. This value is
    stage-specific :

    - 1 to 2 : SDJLevee
    - 2 to 3 : SDJBVP
    - 4 to 5 : SDJRPR
    - 5 to 6 : SDJMatu1
    - 6 to 7 : SDJMatu2

    These parameters are passed explicitly when calling this function.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        num_phase (_type_): _description_

    Returns:
        _type_: _description_
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
    """
    This function increments the phase number.

    When the phase number is not 0, and if changePhase is 1 (meaning that we are
    at a phase transition day), and initPhase is 0 (meaning that the phase
    number has not been incremented yet this day), the phase number is
    incremented by 1. Also, the phase change flag initPhase is set to 1. 

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
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
    """
    This function stores the present thermal time threshold in the
    seuilTempPhasePrec variable.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        num_phase (_type_): _description_

    Returns:
        _type_: _description_
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
    """
    This function manages phase change from phases number 1 to 2.

    First, it flags the day for phase change : If numPhase is 1 and sum of
    thermal time is above the threshold (which value comes here from the
    previous function testing_for_initialization), we set changePhase of this
    particular day to 1.

    Second, we update the thermal time to next phase : if numPhase is 1 and
    changePhase is 1 (meaning that we are at the transition day between phases 1
    and 2), we set the sum of thermal time to the next phase as SDJLevee ; we
    broadcast the value over remaining days.

    We do it before updating phase number because we need to test what is the
    phase number before updating it

    Third, we update the phase number : if numPhase is different from 0 and
    changePhase is 1 (meaning that we are at the transition day between two
    phases, to the exception of transition day between phases 0 and 1), we
    increment numPhase by 1 ; we broadcast the value over remaining days.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramITK (_type_): _description_
        paramVariete (_type_): _description_

    Returns:
        _type_: _description_
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
    """
    This function manages phase change from phases number 2 to 3.

    It has the same structure as update_pheno_phase_1_to_2, with the exception
    of update_thermal_time_previous_phase function, which is called to store the
    present thermal time threshold in the seuilTempPhasePrec variable.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramITK (_type_): _description_
        paramVariete (_type_): _description_

    Returns:
        _type_: _description_
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
    """
    This function manages phase change from phases number 3 to 4.

    It is specific as phase 3 is photoperiodic ; its length is not computed the
    same way as the other phases. Notably, the phasePhotoper flag is updated
    with the PhotoperSarrahV3() function.

    First, this function flags the day for phase change : If numPhase is 3 and
    the phasePhotoper flag is 0, we set changePhase of this particular day to 1.
    This means the photoperiodic phase is over.

    Second, we update the phasePhotoper flag : if numPhase is 3 and changePhase
    is 1 (meaning that we are at the transition day between phases 3 and 4), we
    set the phasePhotoper flag to 1.

    Third, we update the phase number and flag incrementation using
    increment_phase_number().

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramITK (_type_): _description_
        paramVariete (_type_): _description_

    Returns:
        _type_: _description_
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
    """
    This function manages phase change from phases number 4 to 5.

    It has the same structure as update_pheno_phase_2_to_3.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramITK (_type_): _description_
        paramVariete (_type_): _description_

    Returns:
        _type_: _description_
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
    """
    This function manages phase change from phases number 5 to 6.

    It has the same structure as update_pheno_phase_2_to_3.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramITK (_type_): _description_
        paramVariete (_type_): _description_

    Returns:
        _type_: _description_
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
    """
    This function manages phase change from phases number 6 to 7.

    It has the same structure as update_pheno_phase_2_to_3.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramITK (_type_): _description_
        paramVariete (_type_): _description_

    Returns:
        _type_: _description_
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
    """
    This function manages the evolution of the phenological phases. It is a
    wrapper function that calls the specific functions for each phase.

    This function is called at the beginning of the day and makes the
    phenological phases evolve. For this, it increments the phase number and
    changes the value of the thermal time threshold of the next phase.
    ChangePhase is a boolean informing the model to know if a day is a day of
    phase change, which is used to initialize specific variables in certain
    functions. It includes a generic method for the test of the end of the
    photoperiodic phase. PhasePhotoper = 0 at the end of the photoperiodic phase
    and = 1 at the beginning of the phase.

    Phenological phases used in this model (as for cereal crops) :

    0. from the sowing day to the beginning of the conditions favorable for
       germination, and from the harvest to the end of the simulation (no crop)

    1. from the beginning of the conditions favorable for germination to the day
       of germination (du début des conditions favorables pour la germination au
       jour de la levée)

    2. from the day of germination to the beginning of the photoperiodic phase
       (du jour de la levée au début de la phase photopériodique)
    
    3. from the beginning of the photoperiodic phase to the beginning of the
       reproductive phase
    
    4. from the beginning of the reproductive phase to the beginning of the
       maturation (only for maize and rice) 
    
    5. from the beginning of the maturation to the grain milk stage (du début de
       la maturation au stade grain laiteux)
    
    6. from the grain milk stage to the end of the maturation (du début du stade
       grain laiteux au jour de récolte)
    
    7. the day of the harvest
    
    Notes :

    In the case of multiannual continuous simulations, we do not reinitialize
    the reservoirs, at harvest we put the moisture front at the depth of the
    surface reservoir This allows to keep the rooting constraint phenomenon for
    the following season if there is little rain while having the water stock in
    depth remaining from the previous season.

    This function has been originally translated from the EvalPhenoSarrahV3
    procedure of the phenologie.pas and exmodules.pas files of the Sarra-H
    model, Pascal version.
    """

    
    data = testing_for_initialization(j, data, paramITK, paramVariete)
    data = update_pheno_phase_1_to_2(j, data, paramVariete)
    data = update_pheno_phase_2_to_3(j, data, paramVariete)
    data = update_pheno_phase_3_to_4(j, data)
    data = update_pheno_phase_4_to_5(j, data, paramVariete)
    data = update_pheno_phase_5_to_6(j, data, paramVariete)
    data = update_pheno_phase_6_to_7(j, data, paramVariete)

    return data






def calculate_daily_thermal_time(j, data, paramVariete):
    """calculating daily thermal time
    Translated from the EvalDegresJourSarrahV3 procedure of the phenologie.pas and exmodules.pas files of theSarra-H model, Pascal version.
    Pb de méthode !?
    v1:= ((Max(TMin,TBase)+Min(TOpt1,TMax))/2 -TBase )/( TOpt1 - TBase);
    v2:= (TL - max(TMax,TOpt2)) / (TL - TOpt2);
    v:= (v1 * (min(TMax,TOpt1) - TMin)+(min(TOpt2,max(TOpt1,TMax)) - TOpt1) + v2 * (max(TOpt2,TMax)-TOpt2))/( TMax-TMin);
    DegresDuJour:= v * (TOpt1-TBase);

    
    #   If Tmoy <= Topt2 then
    #      DegresDuJour:= max(min(TOpt1,TMoy),TBase)-Tbase
    #   else
    #      DegresDuJour := (TOpt1-TBase) * (1 - ( (min(TL, TMoy) - TOpt2 )/(TL -TOpt2)));
    #    If (Numphase >=1) then
    #         SomDegresJour := SomDegresJour + DegresDuJour
    #    else SomDegresJour := 0;

    Returns:
        _type_: _description_
    """

    data["ddj"][j,:,:] = xr.where(
        data["tpMoy"][j,:,:] <= paramVariete["TOpt2"],
        np.maximum(np.minimum(paramVariete["TOpt1"], data["tpMoy"][j,:,:]), paramVariete["TBase"]) - paramVariete["TBase"],
        (paramVariete["TOpt1"] - paramVariete["TBase"]) * (1 - ((np.minimum(paramVariete["TLim"], data["tpMoy"][j,:,:]) - paramVariete["TOpt2"]) / (paramVariete["TLim"] - paramVariete["TOpt2"]))),
    ) 

    return data






def calculate_sum_of_thermal_time(j, data, paramVariete):
    """
        Translated from the EvalDegresJourSarrahV3 procedure of the phenologie.pas and exmodules.pas files of the Sarra-H model, Pascal version.
    calculating sum of thermal time
sdj has to be broadcasted or calculated as the first process to be able to use it with pheno correctly

    Note : in SARRA-H, when numPhase > 7, sdj is set to 0 and sdj stops cumulating
    Returns:
        _type_: _description_
    """
    data["sdj"][j:,:,:] = xr.where(
        (j >= data["sowing_date"][j,:,:]) & (data["numPhase"][j,:,:] >= 1),
        data["sdj"][j-1,:,:] + data["ddj"][j,:,:],
        0,
    )
    return data





def update_root_growth_speed(j, data, paramVariete):
    """
    This function updates the root growth speed (vRac, mm/day) according to the
    current phase (numPhase).

    This function has been adapted from the EvalVitesseRacSarraV3 procedure of
    the phenologie.pas and exmodules 1 & 2.pas files of the Sarra-H model,
    Pascal version.

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramVariete (_type_): _description_

    Returns:
        _type_: _description_
    """

    phase_correspondances = {
        1: paramVariete['VRacLevee'],
        2: paramVariete['VRacBVP'],
        3: paramVariete['VRacPSP'],
        4: paramVariete['VRacRPR'],
        5: paramVariete['VRacMatu1'],
        6: paramVariete['VRacMatu2'],
    }

    for phase in range(1,6):
        data["vRac"][j:,:,:] = np.where(
            data["numPhase"][j,:,:] == phase,
            phase_correspondances[phase],
            data["vRac"][j,:,:],
        )

    # phase 0 ou 7
    data["vRac"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 0) | (data["numPhase"][j,:,:] == 7),
        0,
        data["vRac"][j,:,:],
    )

    return data




def update_photoperiodism(j, data, paramVariete):
    """
    This function aims at managing the photoperiodic sensitivity of the crop.

    It first updates the sumPP variable : on the transition day between phase 2
    and 3 (numPhase = 3 and changePhase = 1), the sumPP variable is set to 100.

    Then, we compute the thermal_time_since_previous_phase (thermal time since
    the transition between phases 2 and 3), and the
    time_above_critical_day_length, which is the difference between day length
    and critical day length PPcrit, in decimal hours.
    
    On all days with numPhase = 3 (so including the transition day), the sumPP
    is calculated as a function of thermal_time_since_previous_phase and PPExp
    (attenuator for progressive PSP response to PP ; rarely used in calibration
    procedure, a robust value is 0.17), multiplied by a ratio between the daily
    time above critical day length and the difference between SeuilPP (Upper day
    length limit of PP response) and PPCrit (Lower day length limit to PP
    response). 

    Finally, phasePhotoper is updated : when numPhase = 3 and sumPP is lower than
    PPsens, phasePhotoper is set to 0. PP sensitivity, important variable. Range
    0.3-0.6 is PP sensitive, sensitivity disappears towards values of 0.7 to
    1. Described in Dingkuhn et al. 2008; Euro.J.Agron. (Impatience model)

    This function has been adapted from the PhotoperSarrahV3 procedure of the
    phenologie.pas and exmodules 1 et 2.pas of the Sarra-H model, Pascal version.

    Notes CB : 
    Procedure speciale Vaksman Dingkuhn valable pour tous types de sensibilite
    photoperiodique et pour les varietes non photoperiodique. PPsens varie de
    0,4 a 1,2. Pour PPsens > 2.5 = variété non photoperiodique.
    SeuilPP = 13.5
    PPcrit = 12
    SumPP est dans ce cas une variable quotidienne (et non un cumul)

    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramVariete (_type_): _description_

    Returns:
        _type_: _description_
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
    """
    This functions tests for death of young plants.

    First, for numphase = 2 and changePhase = 1, hence at the transition day
    between phase 1 and 2 at this point of the loop, the nbJourCompte and
    nbjStress variables are set to 0.

    Second, for numPhase equal or above 2, on each day nbJourCompte is
    incremented by 1. Thus this part just count days since emergence.

    Third, for numPhase equal or above 2, for days where nbJourCompte is lower
    than nbjTestSemis and where deltaBiomasseAerienne is negative, the nbjStress
    variable is incremented by 1. Thus, we count the number of days with
    negative deltaBiomasseAerienne since emergence as stress days.

    Finally, for days where nbjStress is equal or higher than
    seuilCstrMortality, the crop is reset by setting numPhase,
    root_tank_capacity and nbjStress to 0.

    This all seems a bit simplistic though, and can be improved.

    This function has been adapted from the MortaliteSarraV3 procedure of the
    bilancarbonsarra.pas and exmodules 1 & 2.pas codes of the Sarra-H model,
    Pascal version.


    Args:
        j (_type_): _description_
        data (_type_): _description_
        paramITK (_type_): _description_
        paramVariete (_type_): _description_

    Returns:
        _type_: _description_
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






