import numpy as np

def EvalIrrigPhase(j, data, paramITK):
    # eauDispo : Quantité journalière d'eau infiltrée dans le sol (moins le ruissellement). Unités : mm 
    
    if paramITK["irrigAuto"]==True : # && (numphase > 0) && (numphase < 6) )

        # pour StockIrr
        data["stockIrr"][:,:,j] = np.where(
            (data["numPhase"][:,:,j]>0) & (data["numPhase"][:,:,j]<6),
            np.where(
                (data["ruRac"][:,:,j] < data["ruSurf"][:,:,j]),
                data["stockSurface"][:,:,j],
                data["stockRac"][:,:,j],
                ),
            data["stockIrr"][:,:,j],
        )

        # pour ruIrr
        data["ruIrr"][:,:,j] = np.where(
            (data["numPhase"][:,:,j]>0) & (data["numPhase"][:,:,j]<6),
            np.where(
                (data["ruRac"][:,:,j] < data["ruSurf"][:,:,j]),
                data["ruSurf"][:,:,j],
                data["ruRac"][:,:,j],
                ),
            data["ruIrr"][:,:,j],
        )

        # pour irrigTotDay
        # on a retiré le calcul de l'arrondi selon la précision recherchée
        # on cast sur j
        data["irrigTotDay"][:,:,j] = np.where(
            (data["numPhase"][:,:,j]>0) & (data["numPhase"][:,:,j]<6) & (data["stockIrr"][:,:,j]/data["ruIrr"][:,:,j] < paramITK["irrigAutoTarget"]),
            np.minimum(np.maximum(0, ((data["ruIrr"][:,:,j] - data["stockIrr"][:,:,j]) * 0.9) - data["correctedIrrigation"][:,:,j]), paramITK["maxIrrig"]),
            data["irrigTotDay"][:,:,j],
        )

    data["irrigTotDay"][:,:,j] = data["correctedIrrigation"][:,:,j] + data["irrigTotDay"][:,:,j]		
    data["eauDispo"][:,:,j] = data["rain"][:,:,j] + data["irrigTotDay"][:,:,j]
    data["sommeIrrig"][:,:,j:] = data["sommeIrrig"][:,:,j] + data["irrigTotDay"][:,:,j]
    
    return data





def rempliMc_evalRunOff(j, data, paramITK, paramTypeSol):

    # rempliMc
    # humSatMc ???
    # biomMc : biomasse mulch, kg/ha
    # stockMc : Stock d'eau dans les résidus (mulch). Unités : mm
    # eauDispo : Quantité journalière d'eau infiltrée dans le sol (moins le ruissellement). Unités : mm 
    # surfMc : ???
    
    # on calcule la quantité maximale d'eau stockable par le mulch en prenant le minimum entre :
    # - l'utilisation d'une fonction de la quantité d'eau disponible qui tend vers eauDispo quand surfMc ou biomMc augmentent
    # - la différence entre la quantité d'eau au point de saturation et le stock d'eau connu du mulch
    # on calcule ensuite l'eau disponible en retranchant l'eau captée si sa valeur est supérieure à 0
    # on incrémente ensuite la quantité d'eau dans le mulch par la quantité d'eau captée
  
    data["eauCaptee"][:,:,j] = np.minimum(
        data["eauDispo"][:,:,j] * (1-np.exp(-paramITK["surfMc"] * data["biomMc"][:,:,j]/1000)),
        (paramITK["humSatMc"] * data["biomMc"][:,:,j]/ 10000) - data["stockMc"][:,:,j],
    )

    data["eauDispo"][:,:,j:] =  np.maximum(data["eauDispo"][:,:,j] - data["eauCaptee"][:,:,j], 0)
    data["stockMc"][:,:,j:] = data["stockMc"][:,:,j] + data["eauCaptee"][:,:,j]
    
    # EvalRunOff
    # rain : pluviométrie (mm)
    # seuilRuiss : Seuil pluie, calcul du ruissellement (cf PourcRuiss) (mm)
    # pourcRuiss : (pct décimal)

    data["lr"][:,:,j] = np.where(
        data["rain"][:,:,j] > paramTypeSol["seuilRuiss"],
        (data["eauDispo"][:,:,j]  - paramTypeSol["seuilRuiss"]) *  paramTypeSol["pourcRuiss"],
        0, #data["lr"][:,:,j],
    )

    data["eauDispo"][:,:,j:] = data["eauDispo"][:,:,j] - data["lr"][:,:,j]
    return data





def EvolRurCstr(j, data, paramITK):

    # dayvrac et deltarur reset à chaque itération ; on traine donc le j sur les autres variables

    # rurac test 1
    data["ruRac"][:,:,j] = np.where(
        (data["changePhase"][:,:,j]==True) & (data["numPhase"][:,:,j]==1),
        paramITK["profRacIni"]/1000*data["ru"][:,:,j],
        data["ruRac"][:,:,j],
    )

    # dayvrac
    #on met à jour la vitesse de croissance racinaire
    # en date de changement de stade, pour le stade = 1, et si la réserve utile racinaire est supérieure
    # à la réserve utile de surface, on met à jour vRac pour que la nouvelle valeur soit contrainte par cstr
    data["dayVrac"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]>0) & np.invert((data["changePhase"][:,:,j]==True) & (data["numPhase"][:,:,j]==1)) & (data["ruRac"][:,:,j]>data["ruSurf"][:,:,j]),
        (data["vRac"][:,:,j] * np.minimum(data["cstr"][:,:,j] + 0.3, 1.0)) / 1000 * data["ru"][:,:,j],
        data["dayVrac"][:,:,j],
    )
    
    # deltarur fait des pics car hum est à plat ?
    # hum est à plat parce que stocktotal est à plat ?
    # deltarur
    data["deltaRur"][:,:,j] = np.where(
        (data["numPhase"][:,:,j]>0) & (data["changePhase"][:,:,j]==True) & (data["numPhase"][:,:,j]==1),
        data["deltaRur"][:,:,j],    
        np.where(
            (data["ruRac"][:,:,j]>data["ruSurf"][:,:,j]),
            np.where(
                (data["hum"][:,:,j] - data["ruRac"][:,:,j]) < data["dayVrac"][:,:,j],
                data["hum"][:,:,j] - data["ruRac"][:,:,j],
                data["dayVrac"][:,:,j],
            ),
            data["vRac"][:,:,j]/1000*data["ru"][:,:,j],
        ),
    )

    # rurac2
    data["ruRac"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]>0),
        np.where(
            (data["changePhase"][:,:,j]==True) & (data["numPhase"][:,:,j]==1),
            data["ruRac"][:,:,j],
            data["ruRac"][:,:,j] + data["deltaRur"][:,:,j],
        ),
        data["ruRac"][:,:,j],
    )
        
    #stockrac
    data["stockRac"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j]>0) & np.invert((data["changePhase"][:,:,j]==True) & (data["numPhase"][:,:,j]==1)),
        np.where(
            (data["ruRac"][:,:,j]>data["ruSurf"][:,:,j]),
            data["stockRac"][:,:,j] + data["deltaRur"][:,:,j],
            np.maximum((data["stockRac"][:,:,j] - data["ruSurf"][:,:,j] / 10) * (data["ruRac"][:,:,j] / data["ruSurf"][:,:,j]), 0),
        ),
        data["stockRac"][:,:,j],
    )

    return data




def rempliRes(j, data):

    # eautranspi est reset à chaque itération à 0
    # stRUmax est reset à la valeur ru à chaque itération
    # on ne cast donc pas ces variables sur j

    data["stRuMax"][:,:,j] = data["ru"][:,:,j] * data["profRu"][:,:,j] / 1000
    
    # on met à jour le stock de surface
        # on cast sur j

    data["stRuSurfPrec"][:,:,j] = data["stockSurface"][:,:,j]
    
    # on met à jour le stock d'eau en surface pour qu'il corresponde au stock de surface mis à jour
    # par l'eau disponible, borné au max par 110% de la réserve utile de surface.
    # on transmet donc la valeur sur j
    # ConsoResSep agit aussi sur cette variable
    data["stockSurface"][:,:,j:] = np.minimum(
        data["stockSurface"][:,:,j] + data["eauDispo"][:,:,j],
        data["ruSurf"][:,:,j] + data["ruSurf"][:,:,j] /10
    )

    # si le stock de surface à j-1 est inférieur à 10% de la réserve utile de surface, 
    # la quantité d'eau transpirable correspond à l'eau disponible moins la différence 
    # entre 1/10e de la réserve utile de surface et le stock de surface, bornée au minimum par 0,
    # sinon la quantité d'eau transpirable est égale à l'eau disponible
        # on cast sur j
    data["eauTranspi"][:,:,j] = np.where(
        data["stRuSurfPrec"][:,:,j] < data["ruSurf"][:,:,j]/10,
        np.maximum(
            0,
            data["eauDispo"][:,:,j] - (data["ruSurf"][:,:,j]/10 - data["stRuSurfPrec"][:,:,j])
            ),
        data["eauDispo"][:,:,j],
    )

    # on met à jour le stock d'eau total sur l'ensemble des réservoirs
    # en ajoutant l'eau transpirable
    # on transmet donc la valeur sur j
    data["stockTotal"][:,:,j:] = data["stockTotal"][:,:,j] + data["eauTranspi"][:,:,j]


    # on met à jour le drainage au delà de la profondeur maximum du réservoir (mm/j) :
    # si le stock total est supérieur à la réserve utile maximale,
    # le drainage vaut la différence entre le stock total et la réserve utile maximale,
    # il est nul sinon
        # on cast sur j
    data["dr"][:,:,j:] = np.where(
        data["stockTotal"][:,:,j] > data["stRuMax"][:,:,j],
        data["stockTotal"][:,:,j] - data["stRuMax"][:,:,j],
        0,
    )

    # on met à jour le stock total (mm) pour le borner par la réserve utile maximale
    # si le stock total est supérieur à la réserve utile maximale du sol, il vaut cette réserve utile max
    # sinon on ne touche pas la valeur
        # on cast sur j
    data["stockTotal"][:,:,j:] = np.where(data["stockTotal"][:,:,j] > data["stRuMax"][:,:,j],
        data["stRuMax"][:,:,j],
        data["stockTotal"][:,:,j],
    )

    # on met à jour la quantité d'eau maximale jusqu'au front d'humectation (mm)
    # on retient à chaque point de temps la valeur max entre la valeur hum précédente et le stock total
        # on cast sur j
    data["hum"][:,:,j:] = np.maximum(data["hum"][:,:,j], data["stockTotal"][:,:,j])


    # on met à jour le Stock d'eau disponible pour la plante das la zone racinaire
    # le stock en zone racinaire est donc le stock total borné au maximum par la réserve utile racinaire, 
    # et borné au maximum par le stock d'eau racinaire
    #? on n'a pas ajouté deux fois l'eautranspi dans stocktotal ? 
    # data["stockRac"][:,:,j] = np.minimum(np.minimum(data["stockTotal"][:,:,j] + data["eauTranspi"][:,:,j], data["ruRac"][:,:,j]), data["stockTotal"][:,:,j])
        # on cast sur j
    data["stockRac"][:,:,j] = np.minimum(np.minimum(data["stockTotal"][:,:,j], data["ruRac"][:,:,j]), data["stockTotal"][:,:,j])
    

    return data




def Evaporation(j, data, paramITK):
    # evalFESW - Fraction d'eau transpirable dans le sol dans la zone enracinée. Unités : m3/m3
    # la fraction transpirable dans la zone enracinée est mise à jour et correspond 
    # au rapport entre stock de surface et 110% de la réserve utile de surface
        # on cast sur j
    data["fesw"][:,:,j] = data["stockSurface"][:,:,j] / (data["ruSurf"][:,:,j] * 1.1)

    # evalKceMc - Part du Kc (ETR/ETo) attribué à l'évaporation du sol. 
    # ltr : Taux de rayonnement transmis au sol. Unités : MJ/MJ
    # cette part du kc dépend linéairement de la quantité de mulch
    # attention, confusion dans le script original entre les variables ltr (rayonnement transmis au sol) et lt (ruissellement journalier) ???
    data["kce"][:,:,j] = paramITK["mulch"] / 100 * data["ltr"][:,:,j] * np.exp(-paramITK["coefMc"] * paramITK["surfMc"] * data["biomMc"][:,:,j]/1000)
        # on cast sur j
    #data["kce"][:,:,j:] = paramITK["mulch"] / 100 * data["lr"][:,:,j] * np.exp(-paramITK["coefMc"] * paramITK["surfMc"] * data["biomMc"][:,:,j]/1000)

    # demandeSol
    # Evaporation potentielle (fn du taux de couverture). Unités : mm/d. 
        # on cast sur j
    data["evapPot"][:,:,j:] = data["etp"][:,:,j] * data["kce"][:,:,j]

    # evapMc
    # on met à jour FEMcW
    # si le stock de mulch est supérieur à 0, femcw  est calculé à partir de l'humidité, de la biomasse
    # et du stock d'eau du mulch
        # on cast sur j
    data["FEMcW"][:,:,j:] = np.where(
        data["stockMc"][:,:,j]>0,
        (paramITK["humSatMc"] * data["biomMc"][:,:,j] * 0.001) / data["stockMc"][:,:,j],
        data["FEMcW"][:,:,j],
    )

    # on met à jour le stock d'eau dans le mulch 
    # si le stock d'eau est non-nul, on
    # bornée au minimum par 0
    # attention, confusion dans le script original entre les variables ltr (rayonnement transmis au sol) et lt (ruissellement journalier) ???
        # on cast sur j
    data["stockMc"][:,:,j:] = np.where(
        data["stockMc"][:,:,j] > 0,
        # np.maximum(0, data["stockMc"][:,:,j] - data["ltr"][:,:,j] * data["etp"][:,:,j] * data["FEMcW"][:,:,j]**2),
        np.maximum(0, data["stockMc"][:,:,j] - data["lr"][:,:,j] * data["etp"][:,:,j] * data["FEMcW"][:,:,j]**2),
        data["stockMc"][:,:,j],
    )

    # evapRuSurf
    #     # on cast sur j
    data["evap"][:,:,j:] = np.minimum(data["evalPot"][:,:,j] * data["fesw"][:,:,j]**2, data["stockSurface"][:,:,j])

    return data




def Transpiration(j, data, paramVariete):

        # on cast tout sur j

    #transpiration
    # EvalFTSW
    data["ftsw"][:,:,j:] = np.where(data["ruRac"][:,:,j] > 0,
                                    data["stockRac"][:,:,j] / data["ruRac"][:,:,j],
                                    0,
                                    )

    # EvolKcpKcIni
    data["kcp"][:,:,j:] = np.maximum(0.3, paramVariete["kcMax"] * (1 - data["ltr"][:,:,j]))

    #demandePlante
    data["trPot"][:,:,j:] = data["kcp"][:,:,j] * data["etp"][:,:,j]

    data["pFact"][:,:,j:] = paramVariete["PFactor"] + 0.04 * (5 - np.maximum(data["kcp"][:,:,j], 1) * data["etp"][:,:,j])
    data["pFact"][:,:,j:] = np.minimum(np.maximum(0.1, data["pFact"][:,:,j]), 0.8)

    data["cstr"][:,:,j:] = np.minimum((data["ftsw"][:,:,j] / (1 - data["pFact"][:,:,j])), 1)
    data["cstr"][:,:,j:] = np.maximum(0, data["cstr"][:,:,j])


    # evalTranspi
    data["tr"][:,:,j:] = data["trPot"][:,:,j] * data["cstr"][:,:,j]

    return data





def ConsoResSep(j, data):
        # on cast tout sur j

    # consoResSep
    data["stockSurface"][:,:,j:] = np.maximum(data["stockSurface"][:,:,j] - data["evap"][:,:,j], 10)

    data["consoRur"][:,:,j:] = np.where(data["evap"][:,:,j] > data["trSurf"][:,:,j],
                                        data["trSurf"][:,:,j],
                                        data["evap"][:,:,j],
                                        )

    data["stockTotal"][:,:,j:] = np.maximum(0, data["stockTotal"][:,:,j] - data["consoRur"][:,:,j])

    data["consoRur"][:,:,j:] = np.where(data["ruRac"][:,:,j] < data["ruSurf"][:,:,j],
                                        data["evap"][:,:,j] * data["stockRac"][:,:,j] / data["ruSurf"][:,:,j],
                                        data["consoRur"][:,:,j],
                                        )

    data["stockRac"][:,:,j:] = np.maximum(0, data["stockRac"][:,:,j] - data["consoRur"][:,:,j])

    data["tr"][:,:,j:] = np.where(data["tr"][:,:,j] > data["stockRac"][:,:,j],
                                    np.maximum(data["stockRac"][:,:,j] - data["tr"][:,:,j], 0),
                                    data["tr"][:,:,j],
                                    )

    data["stockSurface"][:,:,j:] = np.where(data["stockRac"][:,:,j]>0,
                                            np.maximum(data["stockSurface"][:,:,j] - (data["tr"][:,:,j] * np.minimum(data["trSurf"][:,:,j]/data["stockRac"][:,:,j], 1)), 0),
                                            data["stockSurface"][:,:,j],
                                            )
    
    data["stockRac"][:,:,j:] = np.maximum(0, data["stockRac"][:,:,j] - data["tr"][:,:,j])
    data["stockTotal"][:,:,j:] = np.maximum(0, data["stockTotal"][:,:,j] - data["tr"][:,:,j])

    return data




def bilanHydro(j, data, paramITK, paramTypeSol, paramVariete):
    data = EvalIrrigPhase(j, data, paramITK)
    data = rempliMc_evalRunOff(j, data, paramITK, paramTypeSol)
    data = EvolRurCstr(j, data, paramITK)
    data = rempliRes(j, data)
    data = Evaporation(j, data, paramITK)
    data = Transpiration(j, data, paramVariete)
    data = ConsoResSep(j, data)

    return data