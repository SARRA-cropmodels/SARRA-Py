import numpy as np
import copy




def EvalPhenoSarrahV3(j, data_2, paramITK, paramVariete): 
  
  """
  Traduit depuis phenologie.pas

  Cette procédure est appelée en début de journée et fait évoluer les phases
  phénologiques. Pour celà, elle incrémente les numéro de phase et change la
  valeur du seuil de somme de degré jours de la phase suivante.
  ChangePhase est un booléen permettant d'informer le modéle pour connaître
  si un jour est un jour de changement
  de phase. Celé permets d'initialiser les variables directement dans les
  modules spécifiques.
  Méthode générique pour le test de fin de la phase photopériodique.
  PhasePhotoper = 0 en fin de la phase photoper et = 1 en debut de la phase

  --> Stades phénologiques pour les céréales:
  // 0 : du jour de semis au début des conditions favorables pour la germination et de la récolte é la fin de simulation (pas de culture)
  // 1 : du début des conditions favorables pour la germination au jour de la levée
  // 2 : du jour de la levée au début de la phase photopériodique
  // 3 : du début de la phase photopériodique au début de la phase reproductive
  // 4 : du début de la phase reproductive au début de la maturation (seulement pour le mais et riz) Pas pris en compte ici!
  //      sousphase1  de début RPR é RPR/4
  //      sousphase2  de RPR/4 é RPR/2
  //      sousphase3 de RPR/2 é 3/4 RPR
  //      sousphase4 de 3/4 RPR é fin RPR
  // 5 : du début de la maturation au stade grain laiteux
  // 6 : du début du stade grain laiteux au jour de récolte
  // 7 : le jour de la récolte
  Dans le cas des simulations pluriannuelles en continue, on ne réinitialise pas les réservoirs, é la récolte on met le front d'humectation é la profndeur du réservoir de surface
  Cela permet de garder le phénoméne de contrainte d'enracinement pour la saison suivante s'il y a peu de pluie
  tout en ayant le stock d'eau en profondeur restant de la saison précédente.

  Args:
      j (int): numéro du jour depuis le début de la simulation
      data (dict): dictionnaire de matrices numpy
      paramITK (dict): dictionnaire de float

  Returns:
      dict: dictionnaire de matrices numpy
  """

  data = copy.deepcopy(data_2)

  # arrivés au stade 7, on remet les variables phénologiques principales à zero
  data["changePhase"][:,:,j:] = np.where(data["numPhase"][:,:,j] == 7, 0, data["changePhase"][:,:,j])[...,np.newaxis]
  data["sdj"][:,:,j:] = np.where(data["numPhase"][:,:,j] == 7, 0, data["sdj"][:,:,j])[...,np.newaxis]
  data["ruRac"][:,:,j:] = np.where(data["numPhase"][:,:,j] == 7, 0, data["numPhase"][:,:,j])[...,np.newaxis]
  data["nbJourCompte"][:,:,j:] = np.where(data["numPhase"][:,:,j] == 7, 0, data["numPhase"][:,:,j])[...,np.newaxis]
  data["startLock"][:,:,j:] = np.where(data["numPhase"][:,:,j] == 7, 1, data["startLock"][:,:,j])[...,np.newaxis]
  # on laisse cette condition en dernier...
  data["numPhase"][:,:,j:] = np.where(data["numPhase"][:,:,j] == 7, 0, data["numPhase"][:,:,j])[...,np.newaxis]

  

  ###### Initialisation - test phase 0 - germination
  # on teste si on est à la phase 0 et que la quantité d'eau est suffisante
  condition = \
    (data["numPhase"][:,:,j] == 0) & \
    (data["stRuSurf"][:,:,j] - data["ruSurf"][:,:,j] / 10 >= paramITK["seuilEauSemis"]) & \
    (data["startLock"][:,:,j] == 0)
    # (data["stSurf"][:,:,j] - data["ruSurf"][:,:,j] / 10 >= paramITK["seuilEauSemis"])
    # on remplace par la variable correcte
    
  
  # on force alors le numéro de phase sur 1
  data["numPhase"][:,:,j:] = np.where(condition, 1, data["numPhase"][:,:,j])[...,np.newaxis]

  # on flag un changement de phase,
  # ce qui permet de déclencher la mise à jour de la somme de températures de la phase suivante
  data["changePhase"][:,:,j] = np.where(condition, 1, data["changePhase"][:,:,j])

  # on force la somme de températures de la phase suivante sur le paramètre SDJ levée
  data["seuilTempPhaseSuivante"][:,:,j:] = np.where(
    condition,
    paramVariete["SDJLevee"],
    data["seuilTempPhaseSuivante"][:,:,j],
  )[...,np.newaxis]

  # on flag ce changement de phase comme étant celui de l'initiation
  # ce qui permet plus tard de bypasser l'incrémentation du numéro de phase
  data["initPhase"] = data["numPhase"].copy() * 0
  data["initPhase"][:,:,j:] = np.where(
    condition,
    1,
    data["initPhase"][:,:,j]
  )[...,np.newaxis]
  
 

  ###### Marquage des dates de changement de phase
  ### Test phase 2
  condition = \
    (data["numPhase"][:,:,j] == 2) & \
    (data["sdj"][:,:,j] >= data["seuilTempPhaseSuivante"][:,:,j])

  data["changePhase"][:,:,j] = np.where(condition, 1, data["changePhase"][:,:,j])

  ### Test phases 1, 4, 5, 6
  condition = \
    (data["numPhase"][:,:,j] != 0) & \
    (data["numPhase"][:,:,j] != 2) & \
    (data["numPhase"][:,:,j] != 3) & \
    (data["sdj"][:,:,j] >= data["seuilTempPhaseSuivante"][:,:,j])

  data["changePhase"][:,:,j] = np.where(condition, 1, data["changePhase"][:,:,j])

  ### test phase 3
  condition = \
    (data["numPhase"][:,:,j] == 3) & \
    (data["phasePhotoper"][:,:,j] == 0)

  data["changePhase"][:,:,j] = np.where(condition, 1, data["changePhase"][:,:,j])

  
  
  ###### incrémentation de la phase
  condition = \
    (data["numPhase"][:,:,j] != 0) & \
    (data["changePhase"][:,:,j] == 1) & \
    (data["initPhase"][:,:,j] != 1)  

  data["numPhase"][:,:,j:] = np.where(
    condition,
    data["numPhase"][:,:,j] + 1 ,
    data["numPhase"][:,:,j],
  )[...,np.newaxis]

  # on enregistre les sdj de la phase précédente
  data["sommeDegresJourPhasePrec"][:,:,j:] = np.where(
      condition,
      data["seuilTempPhaseSuivante"][:,:,j],
      data["sommeDegresJourPhasePrec"][:,:,j],
  )[...,np.newaxis]



  ### on met à jour les températures de changement de phase
  # phase 1
  condition = \
    (data["numPhase"][:,:,j] == 1) & \
    (data["changePhase"][:,:,j] == 1)

  data["seuilTempPhaseSuivante"][:,:,j:] = np.where(
      condition,
      paramVariete["SDJLevee"],
      data["seuilTempPhaseSuivante"][:,:,j]
  )[...,np.newaxis]

  # phase 2
  condition = \
    (data["numPhase"][:,:,j] == 2) & \
    (data["changePhase"][:,:,j] == 1)

  data["seuilTempPhaseSuivante"][:,:,j:] = np.where(
      condition,
      data["seuilTempPhaseSuivante"][:,:,j] + paramVariete["SDJBVP"],
      data["seuilTempPhaseSuivante"][:,:,j]
  )[...,np.newaxis]

  # phase 3
  condition = \
    (data["numPhase"][:,:,j] == 3) & \
    (data["changePhase"][:,:,j] == 1)

  data["phasePhotoper"][:,:,j] = np.where(
      condition,
      1,
      data["phasePhotoper"][:,:,j],
  )  

  # phase 4
  condition = \
    (data["numPhase"][:,:,j] == 4) & \
    (data["changePhase"][:,:,j] == 1)

  data["seuilTempPhaseSuivante"][:,:,j:] = np.where(
      condition,
      data["sdj"][:,:,j] + paramVariete["SDJRPR"],
      data["seuilTempPhaseSuivante"][:,:,j]
  )[...,np.newaxis]

  # phase 5
  condition = \
    (data["numPhase"][:,:,j] == 5) & \
    (data["changePhase"][:,:,j] == 1)

  data["seuilTempPhaseSuivante"][:,:,j:] = np.where(
      condition,
      data["seuilTempPhaseSuivante"][:,:,j] + paramVariete["SDJMatu1"],
      data["seuilTempPhaseSuivante"][:,:,j]
  )[...,np.newaxis]

  # phase 6
  condition = \
    (data["numPhase"][:,:,j] == 6) & \
    (data["changePhase"][:,:,j] == 1)

  data["seuilTempPhaseSuivante"][:,:,j:] = np.where(
      condition,
      data["seuilTempPhaseSuivante"][:,:,j] + paramVariete["SDJMatu2"],
      data["seuilTempPhaseSuivante"][:,:,j]
  )[...,np.newaxis]                                                    




  return data




def EvalDegresJourSarrahV3(j, data, paramVariete):
    
    """
    depuis phenologie.pas 
    
    Pb de méthode !?
    v1:= ((Max(TMin,TBase)+Min(TOpt1,TMax))/2 -TBase )/( TOpt1 - TBase);
    v2:= (TL - max(TMax,TOpt2)) / (TL - TOpt2);
    v:= (v1 * (min(TMax,TOpt1) - TMin)+(min(TOpt2,max(TOpt1,TMax)) - TOpt1) + v2 * (max(TOpt2,TMax)-TOpt2))/( TMax- TMin);
    DegresDuJour:= v * (TOpt1-TBase);

    Returns:
        _type_: _description_
    """

    #     If Tmoy <= Topt2 then
    #      DegresDuJour:= max(min(TOpt1,TMoy),TBase)-Tbase
    #   else
    #      DegresDuJour := (TOpt1-TBase) * (1 - ( (min(TL, TMoy) - TOpt2 )/(TL -TOpt2)));
    #    If (Numphase >=1) then
    #         SomDegresJour := SomDegresJour + DegresDuJour
    #    else SomDegresJour := 0;


    # calcul des degrés jour
    data["ddj"][:,:,j] = np.where(
        data["tpMoy"][:,:,j] <= paramVariete["TOpt2"],
        np.maximum(np.minimum(paramVariete["TOpt1"], data["tpMoy"][:,:,j]), paramVariete["TBase"]) - paramVariete["TBase"],
        (paramVariete["TOpt1"] - paramVariete["TBase"]) * (1 - ((np.minimum(paramVariete["TLim"], data["tpMoy"][:,:,j]) - paramVariete["TOpt2"]) / (paramVariete["TLim"] - paramVariete["TOpt2"]))),
    )  

    # calcul de la somme de degré jour
    # dans sarra-h quand on passe le stade 7, on retombe à 0 et le sdj arrête de cumuler
    data["sdj"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] >= 1,
        data["sdj"][:,:,j] + data["ddj"][:,:,j],
        0,
    )[...,np.newaxis]

    return data





def EvalVitesseRacSarraV3(j, data, paramVariete):
    # d'après phenologie.pas

    # EvalVitesseRacSarraV3

    # phase 1
    data["vRac"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 1,
        paramVariete['VRacLevee'],
        data["vRac"][:,:,j],
    )[...,np.newaxis]

    # phase 2
    data["vRac"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 2,
        paramVariete['VRacBVP'],
        data["vRac"][:,:,j],
    )[...,np.newaxis]

    # phase 3
    data["vRac"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 3,
        paramVariete['VRacPSP'],
        data["vRac"][:,:,j],
    )[...,np.newaxis]

    # phase 4
    data["vRac"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 4,
        paramVariete['VRacRPR'],
        data["vRac"][:,:,j],
    )[...,np.newaxis]

    # phase 5
    data["vRac"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 5,
        paramVariete['VRacMatu1'],
        data["vRac"][:,:,j],
    )[...,np.newaxis]
    
    # phase 6
    data["vRac"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 6,
        paramVariete['VRacMatu2'],
        data["vRac"][:,:,j],
    )[...,np.newaxis]

    # phase 0 ou 7
    #     else
    #  VitesseRacinaire := 0
    #
    data["vRac"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j] == 0) | (data["numPhase"][:,:,j] == 7),
        0,
        data["vRac"][:,:,j],
    )[...,np.newaxis]

    return data




def PhotoperSarrahV3(j, data, paramVariete):
    # depuis phenologie.pas
    """
        {Procedure speciale Vaksman Dingkuhn valable pour tous types de sensibilite
    photoperiodique et pour les varietes non photoperiodique.
    PPsens varie de 0,4 a 1,2. Pour PPsens > 2,5 = variété non photoperiodique.
    SeuilPP = 13.5
    PPcrit = 12
    SumPP est dans ce cas une variable quotidienne (et non un cumul)}
    """

    data["sumPP"][:,:,j] = np.where(
        (data["numPhase"][:,:,j] == 3) & (data["changePhase"][:,:,j] == 1),
        100,
        data["sumPP"][:,:,j],
    )

    data["sumPP"][:,:,j] = np.where(
        (data["numPhase"][:,:,j] == 3),
        (1000 / np.maximum(0.01, data["sdj"][:,:,j] - data ["seuilTempPhasePrec"][:,:,j]) ** paramVariete["PPExp"]) * np.maximum(0, (data["dureeDuJour"][:,:,j] - paramVariete["PPCrit"])) / (paramVariete["SeuilPP"] - paramVariete["PPCrit"]),
        data["sumPP"][:,:,j],
    )

    data["phasePhotoper"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j] == 3) & (data["sumPP"][:,:,j] < paramVariete["PPsens"]),
        0,
        data["phasePhotoper"][:,:,j],
    )[...,np.newaxis]

    return data




def MortaliteSarraV3(j, data, paramITK, paramVariete):

    # test de mortalité juvénile
    #     {
    # Test sur 20 jours
    # D�s que le delta est n�gatif sur 10 jours
    # }

    condition = (data["numPhase"][:,:,j] >= 2) & (data["numPhase"][:,:,j] == 2) & (data["changePhase"][:,:,j] == 1)

    data['nbJourCompte'][:,:,j:] = np.where(
        condition,
        0,
        data['nbJourCompte'][:,:,j],
    )[...,np.newaxis]

    data['nbjStress'][:,:,j:] = np.where(
        condition,
        0,
        data['nbjStress'][:,:,j],
    )[...,np.newaxis]


    condition = (data["numPhase"][:,:,j] >= 2)

    data['nbJourCompte'][:,:,j:] = np.where(
        condition,
        data['nbJourCompte'][:,:,j] + 1,
        data['nbJourCompte'][:,:,j],
    )[...,np.newaxis]


    condition = (data["numPhase"][:,:,j] >= 2) & (data["nbJourCompte"][:,:,j] < paramITK["nbjTestSemis"]) & (data["deltaBiomasseAerienne"][:,:,j] < 0)

    data["nbjStress"][:,:,j:] = np.where(
        condition,
        data["nbjStress"][:,:,j] + 1,
        data["nbjStress"][:,:,j],                           
    )[...,np.newaxis]


    condition = (data["numPhase"][:,:,j] >= 2) & (data["nbjStress"][:,:,j] == paramVariete["seuilCstrMortality"])

    data["numPhase"][:,:,j] = np.where(
        condition,
        0,
        data["numPhase"][:,:,j],
    )

    data["stRurMax"][:,:,j] = np.where(
        condition,
        0,
        data["stRurMax"][:,:,j],
    )

    data["nbjStress"][:,:,j:] = np.where(
        condition,
        0,
        data["nbjStress"][:,:,j],
    )[...,np.newaxis]

    return data