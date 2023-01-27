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
    In this function, we test if the conditions are met to initiate the crop.
    Conditions are : 1) we are in the first phase (0), and 2) the soil moisture is above the threshold for sowing.
    If conditions are met, we initiate the crop by setting the phase number to 1, by flagging a change of phase,and by setting the sum of thermal time of the next phase to be "SDJ levée".

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

    data["initPhase"][j:, :, :] = xr.where(
        condition,
        1,
        data["initPhase"][j, :, :]
    )

    return data


def testing_for_phase_1(j, data, paramITK, paramVariete):

    # testing if the sum of thermal time reaches the threshold needed for the next phase
    # if numPhase is 1 and sum of thermal time is above the threshold, we flag a change of phase
    # then, we update phase number
    # and we update the threshold for the next phase
    condition = \
        (data["numPhase"][j,:,:] == 1) & \
        (data["sdj"][j,:,:] >= data["seuilTempPhaseSuivante"][j,:,:])

    data["changePhase"][j,:,:] = xr.where(condition, 1, data["changePhase"][j,:,:])

    # updating phase number
    condition = \
        (data["numPhase"][j,:,:] != 0) & \
        (data["changePhase"][j,:,:] == 1) & \
        (data["initPhase"][j,:,:] != 1)  

    data["numPhase"][j:,:,:] = np.where(
        condition,
        data["numPhase"][j,:,:] + 1 ,
        data["numPhase"][j,:,:],
    )

    # updating temp threshold
    condition = \
        (data["numPhase"][j,:,:] == 1) & \
        (data["changePhase"][j,:,:] == 1)

    data["seuilTempPhaseSuivante"][j:,:,:] = np.where(
        condition,
        paramVariete["SDJLevee"],
        data["seuilTempPhaseSuivante"][j,:,:]
    )       
    
    return data



def EvalPhenoSarrahV3(j, data, paramITK, paramVariete): 
  
    """
    Translated from the EvalPhenoSarrahV3 procedure of the phenologie.pas and exmodules.pas files of the Sarra-H model, Pascal version.

    Cette procédure est appelée en début de journée et fait évoluer les phases
    phénologiques. Pour celà, elle incrémente les numéro de phase et change la
    valeur du seuil de somme de degré jours de la phase suivante.
    ChangePhase est un booléen permettant d'informer le modéle pour connaître
    si un jour est un jour de changement de phase. Cela permet d'initialiser les variables directement dans les  modules spécifiques.
    Méthode générique pour le test de fin de la phase photopériodique.
    PhasePhotoper = 0 en fin de la phase photoper et = 1 en debut de la phase

    This procedure is called at the beginning of the day to evolve the phenological phases.
    To do so, it computes if the sum of thermal time reaches the threshold needed for the next phenological phase.
    ChangePhase is a boolean informing the model to know if a day is a day of phase change.
    If yes, it increments the phase number and updates thermal time threshold needed to reach the next phase.
    
    PhasePhotoper = 0 at the end of the photoper phase and = 1 at the beginning of the phase

    Phenological phases used in this model (as for cereal crops) :

    0 : from the sowing day to the beginning of the conditions favorable for germination,
        and from the harvest to the end of the simulation (no crop)
    1 : from the beginning of the conditions favorable for germination to the day of germination
        (du début des conditions favorables pour la germination au jour de la levée)
    2 : from the day of germination to the beginning of the photoperiodic phase
        (du jour de la levée au début de la phase photopériodique)
    3 : from the beginning of the photoperiodic phase to the beginning of the reproductive phase
    4 : from the beginning of the reproductive phase to the beginning of the maturation (only for maize and rice) 
    5 : from the beginning of the maturation to the grain milk stage
        (du début de la maturation au stade grain laiteux)
    6 : from the grain milk stage to the end of the maturation
        (du début du stade grain laiteux au jour de récolte)
    7 : the day of the harvest
    
    In the case of multiannual continuous simulations, we do not reinitialize the reservoirs, at harvest we put the moisture front at the depth of the surface reservoir
    This allows to keep the rooting constraint phenomenon for the following season if there is little rain
    while having the water stock in depth remaining from the previous season.
    """

    # performing deepcopy to manage mutability of the xarray dataset
    # data = data.copy(deep=True)

    # data = reset(j, data)

    
    data = testing_for_initialization(j, data, paramITK, paramVariete)

    


    def testing_for_phase_2(j, data, paramITK, paramVariete):

        condition = \
            (data["numPhase"][j,:,:] == 2) & \
            (data["sdj"][j,:,:] >= data["seuilTempPhaseSuivante"][j,:,:])

        data["changePhase"][j,:,:] = xr.where(condition, 1, data["changePhase"][j,:,:])
        
        return data

    
    def testing_for_phase_3(j, data, paramITK, paramVariete):

        condition = \
            (data["numPhase"][j,:,:] == 3) & \
            (data["phasePhotoper"][j,:,:] == 0)

        data["changePhase"][j,:,:] = xr.where(condition, 1, data["changePhase"][j,:,:])
        
        return data

    
    def testing_for_phase_4(j, data, paramITK, paramVariete):

        condition = \
            (data["numPhase"][j,:,:] == 4) & \
            (data["sdj"][j,:,:] >= data["seuilTempPhaseSuivante"][j,:,:])

        data["changePhase"][j,:,:] = xr.where(condition, 1, data["changePhase"][j,:,:])
        
        return data


    def testing_for_phase_5(j, data, paramITK, paramVariete):

        condition = \
            (data["numPhase"][j,:,:] == 5) & \
            (data["sdj"][j,:,:] >= data["seuilTempPhaseSuivante"][j,:,:])

        data["changePhase"][j,:,:] = xr.where(condition, 1, data["changePhase"][j,:,:])
        
        return data

    def testing_for_phase_6(j, data, paramITK, paramVariete):

        condition = \
            (data["numPhase"][j,:,:] == 6) & \
            (data["sdj"][j,:,:] >= data["seuilTempPhaseSuivante"][j,:,:])

        data["changePhase"][j,:,:] = xr.where(condition, 1, data["changePhase"][j,:,:])
        
        return data

    # ### Phase transitions
    # # Testing for phase 2
    # condition = \
    #     (data["numPhase"][j,:,:] == 2) & \
    #     (data["sdj"][j,:,:] >= data["seuilTempPhaseSuivante"][j,:,:])

    # data["changePhase"][j,:,:] = np.where(condition, 1, data["changePhase"][j,:,:])

    # ### Test phases 1, 4, 5, 6
    # condition = \
    #     (data["numPhase"][j,:,:] != 0) & \
    #     (data["numPhase"][j,:,:] != 2) & \
    #     (data["numPhase"][j,:,:] != 3) & \
    #     (data["sdj"][j,:,:] >= data["seuilTempPhaseSuivante"][j,:,:])

    # data["changePhase"][j,:,:] = np.where(condition, 1, data["changePhase"][j,:,:])

    # ### test phase 3
    # condition = \
    #     (data["numPhase"][j,:,:] == 3) & \
    #     (data["phasePhotoper"][j,:,:] == 0)

    # data["changePhase"][j,:,:] = np.where(condition, 1, data["changePhase"][j,:,:])

    
    
    # ###### incrémentation de la phase
    # condition = \
    #     (data["numPhase"][j,:,:] != 0) & \
    #     (data["changePhase"][j,:,:] == 1) & \
    #     (data["initPhase"][j,:,:] != 1)  

    # data["numPhase"][j:,:,:] = np.where(
    #     condition,
    #     data["numPhase"][j,:,:] + 1 ,
    #     data["numPhase"][j,:,:],
    # )##[np.newaxis,...]

    # # on enregistre les sdj de la phase précédente
    # data["sommeDegresJourPhasePrec"][j:,:,:] = np.where(
    #     condition,
    #     data["seuilTempPhaseSuivante"][j,:,:],
    #     data["sommeDegresJourPhasePrec"][j,:,:],
    # )#[np.newaxis,...]



    # ### on met à jour les températures de changement de phase
    # # phase 1
    # condition = \
    #     (data["numPhase"][j,:,:] == 1) & \
    #     (data["changePhase"][j,:,:] == 1)

    # data["seuilTempPhaseSuivante"][j:,:,:] = np.where(
    #     condition,
    #     paramVariete["SDJLevee"],
    #     data["seuilTempPhaseSuivante"][j,:,:]
    # )#[np.newaxis,...]

    # # phase 2
    # condition = \
    #     (data["numPhase"][j,:,:] == 2) & \
    #     (data["changePhase"][j,:,:] == 1)

    # data["seuilTempPhaseSuivante"][j:,:,:] = np.where(
    #     condition,
    #     data["seuilTempPhaseSuivante"][j,:,:] + paramVariete["SDJBVP"],
    #     data["seuilTempPhaseSuivante"][j,:,:]
    # )#[np.newaxis,...]

    # # phase 3
    # condition = \
    #     (data["numPhase"][j,:,:] == 3) & \
    #     (data["changePhase"][j,:,:] == 1)

    # data["phasePhotoper"][j,:,:] = np.where(
    #     condition,
    #     1,
    #     data["phasePhotoper"][j,:,:],
    # )  

    # # phase 4
    # condition = \
    #     (data["numPhase"][j,:,:] == 4) & \
    #     (data["changePhase"][j,:,:] == 1)

    # data["seuilTempPhaseSuivante"][j:,:,:] = np.where(
    #     condition,
    #     data["sdj"][j,:,:] + paramVariete["SDJRPR"],
    #     data["seuilTempPhaseSuivante"][j,:,:]
    # )#[np.newaxis,...]

    # # phase 5
    # condition = \
    #     (data["numPhase"][j,:,:] == 5) & \
    #     (data["changePhase"][j,:,:] == 1)

    # data["seuilTempPhaseSuivante"][j:,:,:] = np.where(
    #     condition,
    #     data["seuilTempPhaseSuivante"][j,:,:] + paramVariete["SDJMatu1"],
    #     data["seuilTempPhaseSuivante"][j,:,:]
    # )#[np.newaxis,...]

    # # phase 6
    # condition = \
    #     (data["numPhase"][j,:,:] == 6) & \
    #     (data["changePhase"][j,:,:] == 1)

    # data["seuilTempPhaseSuivante"][j:,:,:] = np.where(
    #     condition,
    #     data["seuilTempPhaseSuivante"][j,:,:] + paramVariete["SDJMatu2"],
    #     data["seuilTempPhaseSuivante"][j,:,:]
    # )#[np.newaxis,...]                                                    




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
    Note : in SARRA-H, when numPhase > 7, sdj is set to 0 and sdj stops cumulating
    Returns:
        _type_: _description_
    """
    data["sdj"][j,:,:] = xr.where(
        (j >= data["sowing_date"][j,:,:]) & (data["numPhase"][j,:,:] >= 1),
        data["sdj"][j-1,:,:] + data["ddj"][j,:,:],
        0,
    )
    return data





def EvalVitesseRacSarraV3(j, data, paramVariete):
    # d'après phenologie.pas
    # group 79

    # EvalVitesseRacSarraV3

    # phase 1
    #group 72
    data["vRac"][j:,:,:] = np.where(
        data["numPhase"][j,:,:] == 1,
        paramVariete['VRacLevee'],
        data["vRac"][j,:,:],
    )#[...,np.newaxis]

    # phase 2
    # group 73
    data["vRac"][j:,:,:] = np.where(
        data["numPhase"][j,:,:] == 2,
        paramVariete['VRacBVP'],
        data["vRac"][j,:,:],
    )#[...,np.newaxis]

    # phase 3
    # group 74
    data["vRac"][j:,:,:] = np.where(
        data["numPhase"][j,:,:] == 3,
        paramVariete['VRacPSP'],
        data["vRac"][j,:,:],
    )#[...,np.newaxis]

    # phase 4
    # group 75
    data["vRac"][j:,:,:] = np.where(
        data["numPhase"][j,:,:] == 4,
        paramVariete['VRacRPR'],
        data["vRac"][j,:,:],
    )#[...,np.newaxis]

    # phase 5
    # group 76
    data["vRac"][j:,:,:] = np.where(
        data["numPhase"][j,:,:] == 5,
        paramVariete['VRacMatu1'],
        data["vRac"][j,:,:],
    )#[...,np.newaxis]
    
    # phase 6
    # group 77
    data["vRac"][j:,:,:] = np.where(
        data["numPhase"][j,:,:] == 6,
        paramVariete['VRacMatu2'],
        data["vRac"][j,:,:],
    )#[...,np.newaxis]

    # phase 0 ou 7
    #     else
    #  VitesseRacinaire := 0
    #
    # group 78
    data["vRac"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 0) | (data["numPhase"][j,:,:] == 7),
        0,
        data["vRac"][j,:,:],
    )#[...,np.newaxis]

    return data




def PhotoperSarrahV3(j, data, paramVariete):
    # depuis phenologie.pas
    # group 142
    """
        {Procedure speciale Vaksman Dingkuhn valable pour tous types de sensibilite
    photoperiodique et pour les varietes non photoperiodique.
    PPsens varie de 0,4 a 1,2. Pour PPsens > 2,5 = variété non photoperiodique.
    SeuilPP = 13.5
    PPcrit = 12
    SumPP est dans ce cas une variable quotidienne (et non un cumul)}
    """
    # group 139
    data["sumPP"][j,:,:] = np.where(
        (data["numPhase"][j,:,:] == 3) & (data["changePhase"][j,:,:] == 1),
        100,
        data["sumPP"][j,:,:],
    )

    # group 140
    data["sumPP"][j,:,:] = np.where(
        (data["numPhase"][j,:,:] == 3),
        (1000 / np.maximum(0.01, data["sdj"][j,:,:] - data["seuilTempPhasePrec"][j,:,:]) ** paramVariete["PPExp"]) * np.maximum(0, (data["dureeDuJour"][j,:,:] - paramVariete["PPCrit"])) / (paramVariete["SeuilPP"] - paramVariete["PPCrit"]),
        data["sumPP"][j,:,:],
    )

    # group 141
    data["phasePhotoper"][j:,:,:] = np.where(
        (data["numPhase"][j,:,:] == 3) & (data["sumPP"][j,:,:] < paramVariete["PPsens"]),
        0,
        data["phasePhotoper"][j,:,:],
    )#[...,np.newaxis]

    return data




def MortaliteSarraV3(j, data, paramITK, paramVariete):
    # group 150
    # test de mortalité juvénile
    #     {
    # Test sur 20 jours
    # D�s que le delta est n�gatif sur 10 jours
    # }

    condition = (data["numPhase"][j,:,:] >= 2) & (data["numPhase"][j,:,:] == 2) & (data["changePhase"][j,:,:] == 1)

    # group 143
    data['nbJourCompte'][j:,:,:] = np.where(
        condition,
        0,
        data['nbJourCompte'][j,:,:],
    )#[...,np.newaxis]

    # group 144
    data['nbjStress'][j:,:,:] = np.where(
        condition,
        0,
        data['nbjStress'][j,:,:],
    )#[...,np.newaxis]


    condition = (data["numPhase"][j,:,:] >= 2)

    # group 145
    data['nbJourCompte'][j:,:,:] = np.where(
        condition,
        data['nbJourCompte'][j,:,:] + 1,
        data['nbJourCompte'][j,:,:],
    )#[...,np.newaxis]


    condition = (data["numPhase"][j,:,:] >= 2) & (data["nbJourCompte"][j,:,:] < paramITK["nbjTestSemis"]) & (data["deltaBiomasseAerienne"][j,:,:] < 0)

    # group 146
    data["nbjStress"][j:,:,:] = np.where(
        condition,
        data["nbjStress"][j,:,:] + 1,
        data["nbjStress"][j,:,:],                           
    )#[...,np.newaxis]


    condition = (data["numPhase"][j,:,:] >= 2) & (data["nbjStress"][j,:,:] == paramVariete["seuilCstrMortality"])

    # group 147
    data["numPhase"][j,:,:] = np.where(
        condition,
        0,
        data["numPhase"][j,:,:],
    )

    # group 148
    #! renaming stRurMax with root_tank_capacity
    #// data["stRurMax"][j,:,:] = np.where(
    data["root_tank_capacity"][j,:,:] = np.where(
        condition,
        0,
        #// data["stRurMax"][j,:,:],
        data["root_tank_capacity"][j,:,:],
    )

    # group 149
    data["nbjStress"][j:,:,:] = np.where(
        condition,
        0,
        data["nbjStress"][j,:,:],
    )#[...,np.newaxis]

    return data






