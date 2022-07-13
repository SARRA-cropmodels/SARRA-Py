import numpy as np

def EvalDegresJourSarrahV3(j, data, paramVariete):
    
    # calcul des degrés jour
    data["ddj"][:,:,j] = np.where(
        data["tpMoy"][:,:,j] <= paramVariete["TOpt2"],
        np.maximum(np.minimum(paramVariete["TOpt1"], data["tpMoy"][:,:,j]), paramVariete["TBase"]) - paramVariete["TBase"],
        (paramVariete["TOpt1"] - paramVariete["TBase"]) * (1 - ((np.minimum(paramVariete["TLim"], data["tpMoy"][:,:,j]) - paramVariete["TOpt2"])
            / (paramVariete["TLim"] - paramVariete["TOpt2"]))),
    )  

    # calcul de la somme de degré jour
    data["sdj"][:,:,j] = np.where(
        data["numPhase"][:,:,j] >= 1,
        data["sdj"][:,:,j-1] + data["ddj"][:,:,j],
        0,
    )

    return data



def EvalPhenoSarrahV3(j, data, paramITK, paramVariete):
    """	    
    EvolPhenoSarrahV3
	7 phases déterminent les processus de développement de la plante. 
	Elles sont déterminées en fonction d'un seuil de somme de degrés jours uiltempphasesuivante) et,pour la phase 3, de la photopériode.
	ChangePhase=1 si la phase a changé le jour même, sinon 0.
	modification 28/07/2015 retire rusurf/10 dans test semis	
    """

    ### détermination des dates de changement de phase

    # test phase 0 - germination
    condition = (data["numPhase"][:,:,j]==0) & (data["stockSurface"][:,:,j] - data["ruSurf"][:,:,j] / 10 >= paramITK["seuilEauSemis"])
    data["changePhase"][:,:,j] = np.where(condition, 1, data["changePhase"][:,:,j])
    data["seuilTempPhaseSuivante"][:,:,j:] = np.where(condition, paramVariete["SDJLevee"], data["seuilTempPhaseSuivante"][:,:,j])

    # test phase 1 (identique test phase 4 et +)
    condition = (data["numPhase"][:,:,j]==1) & (data["sdj"][:,:,j] >= data["seuilTempPhaseSuivante"][:,:,j])
    data["changePhase"][:,:,j] = np.where(condition, 1, data["changePhase"][:,:,j])

    # test phase 2
    condition = (data["numPhase"][:,:,j]==2) & (data["sdj"][:,:,j] >= data["seuilTempPhaseSuivante"][:,:,j])
    data["changePhase"][:,:,j] = np.where(condition, 1, data["changePhase"][:,:,j])

    # test phase 3
    condition = (data["numPhase"][:,:,j]==3) & (data["phasePhotoper"][:,:,j] == 0)
    data["changePhase"][:,:,j] = np.where(condition, 1, data["changePhase"][:,:,j])

    # test phase 4 et +
    condition = (data["numPhase"][:,:,j]>=4) & (data["sdj"][:,:,j] >= data["seuilTempPhaseSuivante"][:,:,j])
    data["changePhase"][:,:,j] = np.where(condition, 1, data["changePhase"][:,:,j])



    ### la phase a changé, on met à jour les seuils de test de changement de phase
    
    data["sommeDegresJourPhasePrec"][:,:,j:] = np.where(
        data["changePhase"][:,:,j] == 1,
        data["seuilTempPhaseSuivante"][:,:,j],
        data["sommeDegresJourPhasePrec"][:,:,j],
    )

    data["numPhase"][:,:,j:] = np.where(
        data["changePhase"][:,:,j] == 1,
        data["numPhase"][:,:,j] + 1 ,
        data["numPhase"][:,:,j],
    )

    # phase 1
    data["seuilTempPhaseSuivante"][:,:,j:] = np.where(
        (data["changePhase"][:,:,j]==1) & (data["numPhase"][:,:,j]==1),
        paramVariete["SDJLevee"],
        data["seuilTempPhaseSuivante"][:,:,j]
    )

    # phase 2
    data["seuilTempPhaseSuivante"][:,:,j:] = np.where(
        (data["changePhase"][:,:,j]==1) & (data["numPhase"][:,:,j]==2),
        data["seuilTempPhaseSuivante"][:,:,j] + paramVariete["SDJBVP"],
        data["seuilTempPhaseSuivante"][:,:,j]
    )  

    # phase 4
    data["seuilTempPhaseSuivante"][:,:,j:] = np.where(
        (data["changePhase"][:,:,j]==1) & (data["numPhase"][:,:,j]==4),
        data["sdj"][:,:,j] + paramVariete["SDJRPR"],
        data["seuilTempPhaseSuivante"][:,:,j]
    ) 

    # phase 5
    data["seuilTempPhaseSuivante"][:,:,j:] = np.where(
        (data["changePhase"][:,:,j]==1) & (data["numPhase"][:,:,j]==5),
        data["seuilTempPhaseSuivante"][:,:,j] + paramVariete["SDJMatu1"],
        data["seuilTempPhaseSuivante"][:,:,j]
    )

    # phase 6
    data["seuilTempPhaseSuivante"][:,:,j:] = np.where(
        (data["changePhase"][:,:,j]==1) & (data["numPhase"][:,:,j]==6),
        data["seuilTempPhaseSuivante"][:,:,j] + paramVariete["SDJMatu2"],
        data["seuilTempPhaseSuivante"][:,:,j]
    )                                                    



    data["phasePhotoper"][:,:,j] = np.where(
        (data["changePhase"][:,:,j]==1) & (data["numPhase"][:,:,j]==3),
        1,
        data["phasePhotoper"][:,:,j],
    )           

    data["nbjStress"][:,:,j:] = np.where(
        (data["changePhase"][:,:,j]==1) & (data["numPhase"][:,:,j]==7),
        paramVariete["seuilCstrMortality"] + 1,
        data["nbjStress"][:,:,j],
    )

    data["dateRecolte"][:,:,j] = np.where(
        (data["changePhase"][:,:,j]==1) & (data["numPhase"][:,:,j]==7),
        j,
        data["dateRecolte"][:,:,j],
    )
    
    return data                            




def PPTmoySarrahV3(j, data, paramVariete, paramITK):
    """
	PPTmoySarrahV3
	Remplace photopériode: à partir de la fin de la saison des pluies on estime la durée de photopériode
	on déduit de la date de fin de saison la date de fin de la phase photoper fn (Somme degrés Jours phases Matu + RPR, TmoyMatu), 
	on estime donc des variétés virtuelles
    """

    # on calcule le jour de la fin de la photopériode
    data["jourFinPP"][:,:,j:] = np.where(
        data["phasePhotoper"][:,:,j] == 1,
        paramITK["dateFin"] - ((paramVariete["SDJMatu1"] + paramVariete["SDJMatu2"] + paramVariete["SDJRPR"]) / (data["TMoyMatu"][:,:,j] - paramVariete["TBase"])),
        data["jourFinPP"][:,:,j],
    )

    # on corrige les dates inférieures à 0 en rajoutant 365 j
    data["jourFinPP"][:,:,j] = np.where(
        (data["phasePhotoper"][:,:,j] == 1) & (data["jourFinPP"][:,:,j]<0),
        365 + data["jourFinPP"][:,:,j],
        data["jourFinPP"][:,:,j],
    )

    data["phasePhotoper"][:,:,j] = np.where(
                                    (data["phasePhotoper"][:,:,j] == 1),
                                    np.where(
                                        j > data["jourFinPP"][:,:,j],
                                        0,
                                        data["phasePhotoper"][:,:,j],
                                    ) if paramVariete["PPSens"] <= 1 else 0,
                                    data["phasePhotoper"][:,:,j],
                                    )

    data["changePhase"][:,:,j] = np.where(
                                    (data["phasePhotoper"][:,:,j] == 1),
                                    np.where(
                                        j > data["jourFinPP"][:,:,j],
                                        1,
                                        data["changePhase"][:,:,j],
                                    ) if paramVariete["PPSens"] <= 1 else 0,
                                    data["changePhase"][:,:,j],
                                    )

    return data





def MortaliteSarraV3(j, data, paramITK):

    # test de mortalité juvénile

    data['nbJourCompte'][:,:,j:] = np.where(
        data["numPhase"][:,:,j] == 2,
        data['nbJourCompte'][:,:,j] + 1,
        data['nbJourCompte'][:,:,j],
    )

    data["nbjStress"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j] == 2) & (data["nbJourCompte"][:,:,j] < paramITK["nbjTestSemis"]) & (data["deltaBiomasseAerienne"][:,:,j] < 0),
        data["nbjStress"][:,:,j] + 1,
        data["nbjStress"][:,:,j],                           
    )

    data["nbJourCompte"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j] == 2) & (data["nbjStress"][:,:,j] == paramITK["seuilCstrMortality"]),
        0,
        data["nbJourCompte"][:,:,j],
    )

    data["numPhase"][:,:,j] = np.where(
        (data["numPhase"][:,:,j] == 2) & (data["nbjStress"][:,:,j] == paramITK["seuilCstrMortality"]),
        0,
        data["numPhase"][:,:,j],
    )

    data["ruRac"][:,:,j] = np.where(
        (data["numPhase"][:,:,j] == 2) & (data["nbjStress"][:,:,j] == paramITK["seuilCstrMortality"]),
        0,
        data["ruRac"][:,:,j],
    )

    data["nbjStress"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j] == 2) & (data["nbjStress"][:,:,j] == paramITK["seuilCstrMortality"]),
        0,
        data["nbjStress"][:,:,j],
    )

    return data
                                    





def bilanPheno(j, data, paramITK, paramTypeSol, paramVariete):
	

    data['numPhase'][:,:,j:] = np.where(
                                    data['numPhase'][:,:,j]==7,
                                    0,
                                    data['numPhase'][:,:,j],
                                    )


    data['ruRac'][:,:,j:] = np.where(
                                    data['numPhase'][:,:,j]==7,
                                    0,
                                    data['ruRac'][:,:,j],
                                    )

    data['nbJourCompte'][:,:,j:] = np.where(
                                    data['numPhase'][:,:,j]==7,
                                    0,
                                    data['nbJourCompte'][:,:,j],
                                    )

    
    # for variable in list(data) :
    #     data[variable][:,:,j:] = np.where(
    #         data["nbjStress"][:,:,j] > paramVariete['seuilCstrMortality'],
    #         0,
    #         data[variable][:,:,j],
    #     )
    
    # if (j >= (dateDebut + varDateSemis) && nbjStress < paramVariete.seuilCstrMortality ){
	

    data = EvalDegresJourSarrahV3(j, data, paramVariete)
    data = EvalPhenoSarrahV3(j, data, paramITK, paramVariete)
    data = PPTmoySarrahV3(j, data, paramVariete, paramITK)
    data = MortaliteSarraV3(j, data, paramITK)

    # bilan carbo

    # else 

    # bilan hydro

    return data
