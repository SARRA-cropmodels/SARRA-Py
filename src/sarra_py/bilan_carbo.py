import numpy as np

def EvalVitesseRacSarraV3(j, data, paramVariete):
    # EvalVitesseRacSarraV3

    # phase 1
    data["vRac"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 1,
        paramVariete['VRacLevee'],
        data["vRac"][:,:,j],
    )

    # phase 2
    data["vRac"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 2,
        paramVariete['VRacBVP'],
        data["vRac"][:,:,j],
    )

    # phase 3
    data["vRac"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 3,
        paramVariete['VRacPSP'],
        data["vRac"][:,:,j],
    )

    # phase 4
    data["vRac"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 4,
        paramVariete['VRacRPR'],
        data["vRac"][:,:,j],
    )

    # phase 5
    data["vRac"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 5,
        paramVariete['VRacMatu1'],
        data["vRac"][:,:,j],
    )
    
    # phase 6
    data["vRac"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 6,
        paramVariete['VRacMatu2'],
        data["vRac"][:,:,j],
    )

    return data



def EvalConversion(j, data, paramVariete):
    # EvalConversion
    data["KAssim"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 2,
        1,
        data["KAssim"][:,:,j],
    )

    data["KAssim"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 3,
        paramVariete['txAssimBVP'],
        data["KAssim"][:,:,j],
    )

    data["KAssim"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 4,
        paramVariete['txAssimBVP'],
        data["KAssim"][:,:,j],
    )

    data["KAssim"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 5,
        paramVariete["txAssimBVP"] + (data['sdj'][:,:,j] - data['sommeDegresJourPhasePrec'][:,:,j]) * (paramVariete['txAssimMatu1'] -  paramVariete['txAssimBVP']) / (data['seuilTempPhaseSuivante'][:,:,j] - data['sommeDegresJourPhasePrec'][:,:,j]),
        data["KAssim"][:,:,j],
    )

    data["KAssim"][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 6,
        paramVariete["txAssimMatu1"] + (data["sdj"][:,:,j] - data["sommeDegresJourPhasePrec"][:,:,j]) * (paramVariete["txAssimMatu2"] - paramVariete["txAssimMatu1"]) / (data["seuilTempPhaseSuivante"][:,:,j] - data["sommeDegresJourPhasePrec"][:,:,j]),
        data["KAssim"][:,:,j],
    )

    data["conv"][:,:,j:] = data["KAssim"][:,:,j] * paramVariete["txConversion"]

    return data




def EvalLtr(j, data, paramVariete):
    # EvalLtr + EvalParIntercetpe+ EvalAssimPot+ EvalAssimSarrahV3
    # estimation de l'assimilation en fonction du rayonnement, réduite par le stress hydrique
    # ltr : Taux de rayonnement transmis au sol. Unités : MJ/MJ
    # initialiser ltr avec des 1 ?
    data["ltr"][:,:,j] = np.exp(-paramVariete["kdf"] * data["lai"][:,:,j])

    # KPar remplacé par 0.5 attention ajouter Rg 
    data["parIntercepte"][:,:,j] = 0.5 * (1 - data["ltr"][:,:,j]) * data["rgcalc"][:,:,j]
    data["assimPot"][:,:,j:] = data["parIntercepte"][:,:,j] * data["conv"][:,:,j] * 10

    data["assim"][:,:,j] = np.where(
        data["trPot"][:,:,j] > 0,
        data["assimPot"][:,:,j] * data["tr"][:,:,j] / data["trPot"][:,:,j],
        0,
    )

    return data




def EvalRespMaintSarrahV3(j, data, paramVariete, paramITK):

    # on cast sur j
    data["dRespMaint"][:,:,j:] =  ((paramVariete["txRespMaint"] * data["biomasseTotale"][:,:,j] * (2**(data["tMoy"][:,:,j] - paramVariete["tempMaint"]) / 10))) + (paramVariete["txRespMaint"] * data["biomasseFeuilles"][:,:,j] * (2**(data["tMoy"][:,:,j] -  paramVariete["tempMaint"]) / 10))

    # Question pourquoi > 4 tous le s !!! si pas de feuilles mort !!! 
    # # on cast sur j	
    data["dRespMaint"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j] > 4) & (data["biomasseFeuilles"][:,:,j]==0),
        0,
        data["dRespMaint"][:,:,j],
    )

    #biomasse totale en kg/ha
    # on initialise en date du passage à la phase 2,
    # sino, biomasse totale fonction de la biomasse totale t-1 
    data["biomasseTotale"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]==2) & (data["changePhase"][:,:,j]==1),
        paramITK["densite"] *  paramVariete["txResGrain"] *  paramVariete["poidsSecGrain"] / 1000,
        data["biomasseTotale"][:,:,j]  + (data["assim"][:,:,j] - data["dRespMaint"][:,:,j]),
    )

    # on cast sur j
    data["deltaBiomasseTotale"][:,:,j:] = (data["assim"][:,:,j] - data["dRespMaint"][:,:,j])

    return data




def repartitionAerienRacinaire(j, data, paramVariete):
    
    # on stocke la valeur précédente dans deltaBiomasseAerienne
    # deltabiomasseaerienne est juste la différence entre j et j-1
    data["deltaBiomasseAerienne"][:,:,j:] = data["biomasseAerienne"][:,:,j]

    # la biomasseAerienne est égale, sur les stades 2 à 4, à un coeff borné au max en 0.9
    # fois la biomasse totale
    # en dehors de ces stades, elle vaut la différence entre la biomasse totale
    # et la biomasse aerienne
    # on étend sur j
    data["biomasseAerienne"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]>=2) & (data["numPhase"][:,:,j]<=4),
        np.minimum(0.9, paramVariete["aeroTotPente"] * data["biomasseTotale"][:,:,j] + paramVariete["aeroTotBase"]) * data["biomasseTotale"][:,:,j],
        data["biomasseTotale"][:,:,j] - data["biomasseAerienne"][:,:,j],
    )

    data["deltaBiomasseAerienne"][:,:,j:] = data["biomasseAerienne"][:,:,j] - data["deltaBiomasseAerienne"][:,:,j]
    data["biomasseRacinaire"][:,:,j:] = data["biomasseTotale"][:,:,j] - data["biomasseAerienne"][:,:,j]

    return data




def repartitionFeuilleTige(j, data, paramVariete):

    # on cast sur j
    data["dayBiomLeaf"][:,:,j:]=np.where(
        data["numPhase"][:,:,j]>1,
        data["biomasseFeuilles"][:,:,j],
        data["dayBiomLeaf"][:,:,j],
    )

    # on cast sur j
    data["biomasseFeuilles"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]>1) & (data["deltaBiomasseAerienne"][:,:,j]<0),
        np.maximum(0.0, data["biomasseFeuilles"][:,:,j] - (-data["deltaBiomasseAerienne"][:,:,j] + data["reallocation"][:,:,j])	* paramVariete["pcReallocFeuille"]),
        data["biomasseFeuilles"][:,:,j],
    )

    # on cast sur j
    data["biomasseTiges"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]>1) & (data["deltaBiomasseAerienne"][:,:,j]<0),
        np.maximum(0.0, data["biomasseTiges"][:,:,j] - (-data["deltaBiomasseAerienne"][:,:,j] + data["reallocation"][:,:,j])	* paramVariete["pcReallocFeuille"]), #! attention on utilise ici le pcReallocFeuille ?
        data["biomasseTiges"][:,:,j],
    )



    bM = paramVariete["feuilAeroBase"] - 0.1
    cM = (( paramVariete["feuilAeroPente"] * 1000)/ bM + 0.78) / 0.75

    # numphase inférieur ou égal à 4
    # on cast sur j
    data["biomasseFeuilles"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]>1) & (data["deltaBiomasseAerienne"][:,:,j]>=0) & (data["numPhase"][:,:,j]<=4),
        (0.1 + bM * cM**(data["biomasseAerienne"][:,:,j] / 1000)) * data["biomasseAerienne"][:,:,j],
        data["biomasseFeuilles"][:,:,j],
    )

    # on cast sur j
    data["biomasseTiges"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]>1) & (data["deltaBiomasseAerienne"][:,:,j]>=0) & (data["numPhase"][:,:,j]<=4),
        data["biomasseAerienne"][:,:,j] - data["biomasseFeuilles"][:,:,j],
        data["biomasseFeuilles"][:,:,j],
    )

    # on cast sur j
    # condition else : numphase supérieur à 4
    data["biomasseFeuilles"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]>1) & (data["deltaBiomasseAerienne"][:,:,j]>=0) & (data["numPhase"][:,:,j]>4),
        data["biomasseFeuilles"][:,:,j] - data["reallocation"][:,:,j] *  paramVariete["pcReallocFeuille"],
        data["biomasseFeuilles"][:,:,j],
    )
    # on cast sur j
    data["biomasseTiges"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]>1) & (data["deltaBiomasseAerienne"][:,:,j]>=0) & (data["numPhase"][:,:,j]>4),
        data["biomasseTiges"][:,:,j] - (data["reallocation"][:,:,j] * (1-  paramVariete["pcReallocFeuille"])),
        data["biomasseTiges"][:,:,j],
    )
    # on cast sur j
    data["biomasseAerienne"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]>1) & (data["deltaBiomasseAerienne"][:,:,j]>=0) & (data["numPhase"][:,:,j]>4),
        data["biomasseTiges"][:,:,j] + data["biomasseFeuilles"][:,:,j] + data["rdt"][:,:,j],
        data["biomasseAerienne"][:,:,j],
    )

    # on cast sur j
    # else if ?
    data["dayBiomLeaf"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]>1),
        data["biomasseFeuilles"][:,:,j] - data["dayBiomLeaf"][:,:,j],
        data["dayBiomLeaf"][:,:,j], 
    )
    # on cast sur j
    data["biomasseVegetative"][:,:,j:] = data["biomasseTiges"][:,:,j]   + data["biomasseFeuilles"][:,:,j]

    return data




def EvalRdtPotRespSarrahV3(j, data, paramVariete):
        # on cast sur j
    data["biomTotStadeIP"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]==4) & (data["changePhase"][:,:,j]==1),
        data["biomasseTotale"][:,:,j],
        data["biomTotStadeIP"][:,:,j], 
    )
    # on cast sur j
    data["biomasseTotaleStadeF"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]==5) & (data["changePhase"][:,:,j]==1),
        data["biomasseTotale"][:,:,j],
        data["biomasseTotaleStadeF"][:,:,j],
    )
    # on cast sur j
    data["rdtPot"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]==5) & (data["changePhase"][:,:,j]==1),
        (paramVariete["KRdtPotA"] * (data['biomasseTotaleStadeF'][:,:,j] - data['biomTotStadeIP'][:,:,j]) +  paramVariete['KRdtPotB']) + paramVariete['KRdtBiom'] * data['biomasseTotaleStadeF'][:,:,j],
        data["rdtPot"][:,:,j],
    )
    # on cast sur j
    data["rdtPot"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]==5) & (data["changePhase"][:,:,j]==1) & (data["rdtPot"][:,:,j]>data["biomasseTotale"][:,:,j]),
        data["biomasseTotale"][:,:,j],
        data["rdtPot"][:,:,j],
    )
    # on cast sur j
    data["dRdtPot"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]==5) & (data["trPot"][:,:,j]>0),
        np.maximum((data["rdtPot"][:,:,j] * (data["ddj"][:,:,j] /  paramVariete["SDJMatu1"]) * (data["tr"][:,:,j] / data["trPot"][:,:,j])), (data["dRespMaint"][:,:,j] * 0.15)),
        0,
    )

    return data




def EvalReallocationSarrahV3(j, data, paramVariete):
        # on cast sur j
    data["manqueAssim"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j] == 5),
        np.maximum(0, (data["dRdtPot"][:,:,j] -  np.maximum(0.0, data["deltaBiomasseAerienne"][:,:,j]))),
        0,
    )
    # on cast sur j
    data["reallocation"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j] == 5),
        np.minimum(data["manqueAssim"][:,:,j] *  paramVariete["txRealloc"],  np.maximum(0.0, data["biomasseFeuilles"][:,:,j] - 30)),
        0,
    )

    return data




def EvolDayRdtSarraV3(j, data):
    # on cast sur j
    data["rdt"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j] == 5),
        data["rdt"][:,:,j] + np.minimum(data["dRdtPot"][:,:,j],  np.maximum(0.0, data["deltaBiomasseAerienne"][:,:,j]) + data['reallocation'][:,:,j]),
        data["rdt"][:,:,j],
    )

    return data




def EvalSlaSarrahV3_EvolLAIPhases(j, data, paramVariete):

    # on cast sur j
    data["sla"][:,:,j:] = np.where(
        (data["biomasseFeuilles"][:,:,j]>0) & (data["numPhase"][:,:,j]==1) & (data["changePhase"][:,:,j]==1),
        paramVariete["slaMax"],
        data["sla"][:,:,j],
    )
    # on cast sur j
    data["sla"][:,:,j:] = np.where(
        (data["biomasseFeuilles"][:,:,j]>0),
        np.minimum(paramVariete["slaMax"], np.maximum(paramVariete["slaMin"], (data["sla"][:,:,j] -  paramVariete["slaPente"] * (data["sla"][:,:,j] -  paramVariete["slaMin"])) * (data["biomasseFeuilles"][:,:,j] - data["dayBiomLeaf"][:,:,j]) / (data["biomasseFeuilles"][:,:,j] + (paramVariete["slaMax"] + data["sla"][:,:,j])/2 * (data["dayBiomLeaf"][:,:,j] / data["biomasseFeuilles"][:,:,j])))),
        data["sla"][:,:,j],
    )
    # on cast sur j
    data["lai"][:,:,j:] = np.where(
        data["numPhase"][:,:,j]<=1,
        0,
        np.where(
            data["numPhase"][:,:,j]<=6,
            data["biomasseFeuilles"][:,:,j] * data["sla"][:,:,j],
            0,
        )
    )

    return data




def bilanCarbo(j, data, paramITK, paramTypeSol, paramVariete):
    data = EvalVitesseRacSarraV3(j, data, paramVariete)
    data = EvalConversion(j, data, paramVariete)
    data = EvalLtr(j, data, paramVariete)
    data = EvalRespMaintSarrahV3(j, data, paramVariete, paramITK)
    data = repartitionAerienRacinaire(j, data, paramVariete)
    data = repartitionFeuilleTige(j, data, paramVariete)
    data = EvalRdtPotRespSarrahV3(j, data, paramVariete)
    data = EvalReallocationSarrahV3(j, data, paramVariete)
    data = EvolDayRdtSarraV3(j,data)
    data = EvalSlaSarrahV3_EvolLAIPhases(j, data, paramVariete)
    
    return data