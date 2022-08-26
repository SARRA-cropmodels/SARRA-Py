import numpy as np

def InitPlotMc(data, grid_width, grid_height, paramITK, paramTypeSol, duration): # depuis Bileau.pas
    
    # BiomMc := BiomIniMc;
    data["biomMc"] = np.full((grid_width, grid_height, duration), paramITK["biomIniMc"])
    
    # LitTiges := BiomIniMc;
    data["LitTige"] = np.full((grid_width, grid_height, duration), paramITK["biomIniMc"])

    # StSurf := StockIniSurf;
    # data["stSurf"] = np.full((grid_width, grid_height, duration), paramTypeSol["stockIniSurf"])

    # Ltr := 1;
    data["ltr"] = np.full((grid_width, grid_height, duration), 1.0)

    # StRurMax := Ru * ProfRacIni / 1000;
    data["stRurMax"] = np.full((grid_width, grid_height, duration), (paramTypeSol["ru"] * paramITK["profRacIni"] / 1000))

    # RuSurf := EpaisseurSurf / 1000 * Ru;
    data["ruSurf"] = np.full((grid_width, grid_height, duration), (paramTypeSol["epaisseurSurf"] / 1000 * paramTypeSol["ru"]))
    
    # //    PfTranspi := EpaisseurSurf * HumPf;
    # //    StTot := StockIniSurf - PfTranspi/2 + StockIniProf;

    # StTot := StockIniSurf  + StockIniProf;
    #data["stTot"] = np.full((grid_width, grid_height, duration), (paramTypeSol["stockIniSurf"] + paramTypeSol["stockIniProf"]))
    #! modifié pour faire correspondre les résultats de simulation, à remettre en place pour un calcul correct dès que possible
    data["stTot"] = np.full((grid_width, grid_height, duration), (paramTypeSol["stockIniProf"]))
    

    # ProfRU := EpaisseurSurf + EpaisseurProf;
    data["profRu"] = np.full((grid_width, grid_height, duration), (paramTypeSol["epaisseurSurf"] + paramTypeSol["epaisseurProf"]))

    # // modif 10/06/2015  resilience stock d'eau
    # // Front d'humectation egal a RuSurf trop de stress initial
    # //    Hum := max(StTot, StRurMax);
    
    # Hum := max(RuSurf, StRurMax);
    # // Hum mis a profRuSurf
    # Hum := max(StTot, Hum);
    data["hum"] = np.full((grid_width, grid_height, duration),
        np.maximum(
            np.maximum(
                data["ruSurf"],
                data["stRurMax"],
            ),
            data["stTot"],
        )
    )
 
    
    data["humPrec"] = np.copy(data["hum"])

    
    # HumPrec := Hum;
    # StRurPrec := 0;
    # StRurMaxPrec := 0;
    data["stRuPrec"] = np.copy(data["stTot"])
    # //modif 10/06/2015 resilience stock d'eau

    return data





def Meteo0DegToRad(): #pas indispensable
    return None

def Meteo1AVGTempHum(): # pas indispensable
    return None

def Meteo2Decli(): # pas indispensable
    return None

def Meteo3SunPosi():# pas indispensable
    return None

def Meteo4DayLength():# pas indispensable
    return None

def Meteo5SunDistance():# pas indispensable
    return None

def Meteo6RayExtra():# pas indispensable
    return None

def Meteo7RgMax():# pas indispensable
    return None

def Meteo8InsToRg():# pas indispensable
    return None

def Meteo9Par():# pas indispensable
    return None

def MeteoEToFAO():# pas indispensable
    return None






def EvalIrrigPhase(j, data, paramITK):
    """
    depuis bileau.pas

    CB 2014
Modification due � la prise en compte effet Mulch
  Soit on a une irrigation observ�e, soit on calcul la dose d'irrigation
  Elle est calcul�e en fonvtion d'un seuil d'humidit� (IrrigAutoTarget)
  et de possibilit� technique ou choix (MaxIrrig, Precision)
  Dans cette gestion d'irrigation la pluie du jour n'est pas prise en compte

    """
    # EnPlus : Double;
    # CorrectedIrrigation : Double;
    # StockIrr , RuIrr : Double;
    # IrrigTotDay := 0;
    # ces variables sont reset à chaque call de la fonction

    data["correctedIrrigation"][:,:,j] = data["irrigation"][:,:,j].copy()

    # si on est en mode d'irrigation automatique
    # pour stockIrr
    # entre les phases 0 et 6, si la RU racinaire est inférieure à la RU desurface, 
    # autrement dit si les racines ne sont pas encore descendues en dessous del'horizon de surface,
    # le stockIrr vaut le stock de surface ; en somme, on met une borne minimaleau stockIrr.
    # Pour la phase 7, on conserve le stockIrr existant.

    condition = (data["irrigAuto"][:,:,j] == True) & \
        (data["numPhase"][:,:,j] > 0) & \
        (data["numPhase"][:,:,j] < 6)

    data["stockIrr"][:,:,j] = np.where(
        condition,
        np.where(
            (data["stRurMax"][:,:,j] < data["ruSurf"][:,:,j]),
            data["stRuSurf"][:,:,j],
            data["stRur"][:,:,j],
            ),
        data["stockIrr"][:,:,j],
    )

    # pour ruIrr
    # même principe que pour stockIrr, concernant cette fois la réserve utile ;
    # on met donc une borne minimale au ruIrr.
    data["ruIrr"][:,:,j] = np.where(
        condition,
        np.where(
            (data["stRurMax"][:,:,j] < data["ruSurf"][:,:,j]),
            data["ruSurf"][:,:,j],
            data["stRurMax"][:,:,j],
            ),
        data["ruIrr"][:,:,j],
    )

    # pour irrigTotDay
    # entre les phases 0 et 6, si le rapport entre stockIrr et ruIrr est inférieur 
    # au irrigAutoTarget, autrement dit si le remplissage du réservoird'irrigation 
    # est en dessous du recherché, on rajoute 90% de la différence entre stockIrret ruIrr,
    # borné en minimum par 0 et en maximum par maxIrrig. On corrige cetteirrigation par
    # correctedIrrigation.
    # A noter le retrait de la méthode du calcul de l'arrondi selon la précisionrecherchée

    condition = (data["irrigAuto"][:,:,j] == True) & \
        (data["numPhase"][:,:,j] > 0) & \
        (data["numPhase"][:,:,j] < 6) & \
        (data["stockIrr"][:,:,j]/data["ruIrr"][:,:,j] < paramITK["irrigAutoTarget"])


    data["irrigTotDay"][:,:,j] = np.where(
        condition,
        np.minimum(
            np.maximum(
                0,
                ((data["ruIrr"][:,:,j] - data["stockIrr"][:,:,j]) * 0.9) - data["correctedIrrigation"][:,:,j]),
            paramITK["maxIrrig"]
        ),
        data["irrigTotDay"][:,:,j],
    )
    
    # On calcule l'irrigation totale du jour en sommant la correction d'irrigation et l'irrigTotDay
    data["irrigTotDay"][:,:,j] = (data["correctedIrrigation"][:,:,j] + data["irrigTotDay"][:,:,j]).copy()		
   
    
    return data




def PluieIrrig(j, data):
    """
    d'après bileau.pas

    // CB 2014
Hypotheses :
Le mulch ajoute une couche direct sous la pluie et irrig, ici irrigTotDay
qui est l'irrigation observ�e ou calcul�e
d'o� on regroupe les deux avant calcul de remplissage du mulch et ensuite
calcul du ruissellement


    Fonction de calcul de l'eau totale apportée entre la pluie et l'irrigation.

    Args:
        j (_type_): _description_
        data (_type_): _description_

    Returns:
        _type_: _description_
    """

    data["eauDispo"][:,:,j] = (data["rain"][:,:,j] + data["irrigTotDay"][:,:,j]).copy()
    return data




def RempliMc(j, data, paramITK):

    """
    d'après bileau.pas

    Hypotheses :
    � chaque pluie on estime la quantit� d'eau pour saturer le couvert
    on la retire � l'Eaudispo (pluie + irrig)
    On calcul la capacit� maximum de stockage fn de la biomasse et du taux de saturation
    rapport�e en mm (HumSatMc en Kg H2O/Kg biomasse)
    La pluie est en mm unit� :
    1 mm = 1 litre d'eau / m2
    1 mm = 10 tonnes d'eau / hectare = 10 000 kg/ha
    La biomasse est en kg/ha pour se rapporter � la quantit� de pluie capt�e en mm
    KgH2O/Kg Kg/ha et kg/m� on divise par 10 000
    ( pour 3000 kg/ha � HumSat 2.8 kgH2O/kg on a un stockage max de 0.84 mm de pluie !??)
    Cette capacit� a capter est fn du taux de couverture du sol calcul� comme le LTR
    SurfMc est sp�cifi� en ha/t (0.39), on rapporte en ha/kg en divisant par 1000
    On retire alors les mm d'eau capt�es � la pluie incidente.
    Le ruisselement est ensuite calcul� avec l'effet de contrainte du mulch

    eauDispo : Quantité journalière d'eau infiltrée dans le sol (moins le ruissellement). Unités : mm  


    Returns:
        _type_: _description_
    """

    # Var Eaucaptee : double;
    # eaucaptee est donc une variable remise à zero a chaque appel de fonction

    # eauCaptée
    # Détermination de l'eau captée par le mulch ; 
    data["eauCaptee"][:,:,j] = np.minimum(
        data["eauDispo"][:,:,j] * (1 - np.exp(-paramITK["surfMc"] * data["biomMc"][:,:,j] / 1000)),
        (paramITK["humSatMc"] * data["biomMc"][:,:,j]/ 10000) - data["stockMc"][:,:,j],
    )

    # on retranche également à l'eau dispo la lame de ruissellement dans EvalRunOff
    data["eauDispo"][:,:,j:] =  np.maximum(data["eauDispo"][:,:,j] - data["eauCaptee"][:,:,j], 0)[...,np.newaxis]
    
    # il est possible que le stockMc soit nul en fin de boucle car stockMc est aussi
    # mobilisé lors de l'évaporation
    data["stockMc"][:,:,j:] = (data["stockMc"][:,:,j] + data["eauCaptee"][:,:,j]).copy()

    return data




def EvalRunOff(j, data, paramTypeSol):

    """
    d'après bileau.pas

    // CB 2014
    On a regroupé avant la pluie et l'irrigation (a cause de l'effet Mulch)
    si mulch on a enlevé l'eau captée
    oN CALCUL SIMPLEMENT LE RUISSELLEMENT EN FN DE SEUILS
    }
    """

    # lr est reset a zéro en début de calcul, on ne broadcast pas les valeurs
    data["lr"][:,:,j] = np.where(
        data["rain"][:,:,j] > paramTypeSol["seuilRuiss"],
        (data["eauDispo"][:,:,j]  - paramTypeSol["seuilRuiss"]) *  paramTypeSol["pourcRuiss"],
        data["lr"][:,:,j],
    )

    data["eauDispo"][:,:,j:] = (data["eauDispo"][:,:,j] - data["lr"][:,:,j]).copy()

    return data





def EvolRurCstr2(j, data, paramITK):

    """
    d'après bileau.pas

    Modif 10/06/2015  Stres trop fort enracinement
    Trop d'effet de stress en tout début de croissance :
    1) la plantule a des réserves et favorise l'enracinement
    2) dynamique spécifique sur le réservoir de surface
    Cet effet stress sur l'enracinement ne s'applique que quand
    l'enracinement est supérieur é la profondeur du réservoir de surface.
    Effet stres a un effet sur la vitesse de prof d'enracinement au dessus
    d'un certain seuil de cstr (on augmente le cstr de 0.3
    pour que sa contrainte soit affaiblie sur la vitesse)
    La vitesse d'enracinement potentielle de la plante peut etre bloque
    par manque d'eau en profondeur (Hum). La profondeur d'humectation
    est convertie en quantite d'eau maximum equivalente
    // Parametres
    IN:
    Vrac : mm (en mm/jour) : Vitesse racinaire journalière §§ Daily root depth
    Hum : mm Quantité d'eau maximum jusqu'au front d'humectation §§ Maximum water capacity to humectation front
    StRuSurf : mm
    RU : mm/m
    RuSurf : mm/m
    INOUT:
    stRurMax : mm ==== ruRac
    stRur : mm ==== stockRac

    nb : on remet le nom de variables de christian plutôt que celles de Mathieu
    """

    # dayvrac et deltarur reset à chaque itération ; on traine donc le j sur les autres variables

    # rurac/stRurMax partie 1 : réserve utile racinaire maximale à l'initialisation
    # rurac : Capacité maximum d'eau rapporté à la profondeur racinaire en cours §§ Water column that can potentially be strored in soil volume explored by root system
    #
    # au changement de phase entre la phase 0 et la phase 1 (initialisation),
    # la réserve utile racinaire est initialisée en multipliant la profondeur
    # racinaire initiale avec la RU du sol



    data["stRurMax"][:,:,j:] = np.where(
        (data["changePhase"][:,:,j] == 1) & (data["numPhase"][:,:,j] == 1),
        paramITK["profRacIni"] / 1000 * data["ru"][:,:,j],
        data["stRurMax"][:,:,j],
    )

    # dayVrac
    # on met à jour la vitesse de croissance racinaire
    # pour les phases à partir de 1 à l'exclusion de l'initiation, et pour laquelle on a
    # une réserve utile racinaire maximale supérieure à la réserve utile de surface,
    # la vitesse racinaire est définie comme vRac modulée par le cstr modifié
    # 
    # donc une fois que la racine a une réserve utile maximale plus importante que le réservoir de surface, 
    # sa vitesse de croissance racinaire est modulée par le stress hydrique.
    #? pourquoi est ce qu'on a un bornage en [0.3,1] ? 
    condition = (data["numPhase"][:,:,j] > 0) & \
            np.invert((data["numPhase"][:,:,j] == 1) & (data["changePhase"][:,:,j] == 1))
            

    # bornage : d'apres CB ; quand on a de l'eau, la racine s'enfonce ; hypothèse lors d'un fort stress, 
    # la plante pousse plutôt sur les racines que sur le reste. en plus en faisant 0.3 et 1, 
    # cela reviet à dire que jusqu'à 70% de cstr; pas d'effet sur l'enracinement. 
    # on décale donc l'effet de cstr en regard des connaissances que l'on a sur l'impact fort sur la plante. 
    data["dayVrac"][:,:,j] = np.where(
        condition,
        np.where(
            (data["stRurMax"][:,:,j] > data["ruSurf"][:,:,j]),
            (data["vRac"][:,:,j] * np.minimum(data["cstr"][:,:,j] + 0.3, 1.0)) / 1000 * data["ru"][:,:,j],
            data["vRac"][:,:,j] / 1000 * data["ru"][:,:,j],
        ),
        data["dayVrac"][:,:,j],
    )
    
    
    # deltarur 
    # pour les phases à partir de 1 à l'exclusion de l'initiation,
    # et pour lesquelles la différence entre le front d'hymectation et la réserve utile racinaire
    # maximale est inférieure à la vitesse de croissance racinaire,
    # on définit la variation de réserve utile racinaire comme étant 
    # la différence entre le front d'humectation et la réserve utile racinaire maximale
    # sinon, on la définit comme la vitesse de croissance racinaire
    condition = (data["numPhase"][:,:,j] > 0) & \
            np.invert((data["numPhase"][:,:,j] == 1) & (data["changePhase"][:,:,j] == 1))

    
    data["deltaRur"][:,:,j:] = np.where(
        condition,   
        np.where(
            (data["hum"][:,:,j] - data["stRurMax"][:,:,j]) < data["dayVrac"][:,:,j],
            data["hum"][:,:,j] - data["stRurMax"][:,:,j],
            data["dayVrac"][:,:,j],
        ),
        data["deltaRur"][:,:,j],
    )


    # rurac/stRurMax partie 2
    # réserve utile racinaire maximale hors initialisation
    # pour des phases différentes de zéro et hors jour d'initialisation, on définit la 
    # réserve utile racinaire maximale comme étant la réserve utile racinaire maximale précédente
    # que l'on incrémente de la variation de réserve utile racinaire deltaRur

    data["stRurMax"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j] > 0),
        np.where(
            np.invert((data["changePhase"][:,:,j] == 1) & (data["numPhase"][:,:,j] == 1)),
            data["stRurMax"][:,:,j] + data["deltaRur"][:,:,j],
            data["stRurMax"][:,:,j],
        ),
        data["stRurMax"][:,:,j],
    )
    
    
    # stockrac/stRur
    # stock d'eau racinaire
    # pour des phases différentes de zéro et hors jour d'initialisation,
    # et si la réserve utile racinaire maximale est supérieure à la réserve utile de surface,
    # (donc si les racines vont au delà du stock de surface)
    # le stock d'eau racinaire est incrémenté de la variation de réserve utile racinaire deltaRur
    # sinon, si la réserve utile racinaire maximale est inférieure à la réserve utile de surface
    # (donc si les racines restent dans les limites du stock de surface)
    # le stock d'eau racinaire prend pour valeur le stock d'eau de surface moins 1/10e de la réserve utile de surface,
    # multiplié par le rapport entre le stock racinaire maximal et la réserve utile de surface
    # ("on prend au prorata de la profondeur et du stock de surface")

    print("stRur 1",data["stRur"][:,:,j])
    data["stRur"][:,:,j:] = np.where(
        (data["numPhase"][:,:,j] > 0) & np.invert((data["changePhase"][:,:,j] == 1) & (data["numPhase"][:,:,j] == 1)),
        np.where(
            (data["stRurMax"][:,:,j] > data["ruSurf"][:,:,j]),
            data["stRur"][:,:,j] + data["deltaRur"][:,:,j],
            np.maximum((data["stRuSurf"][:,:,j] - data["ruSurf"][:,:,j] / 10) * (data["stRurMax"][:,:,j] / data["ruSurf"][:,:,j]), 0),
        ),
        data["stRur"][:,:,j],
    )
    
    print("stRur 2",data["stRur"][:,:,j])
    

    return data




def rempliRes(j, data):

    # d'après bileau.pas
    #
    # Modif 10/06/2015 prise en compte de stock d'eau r�silient pour les simulation continues
    # Hypoth�se de la MAJ des stock en fn de l'eau r�siliente de l'ann�e pr�c�dente
    # dans le cas des simulations pluri annuelle en continue (NbAn = 1):
    # A la r�colte on recup�re les stock d'eau (StRuPrec), la prof d'Humectation (Humprec)
    # et la prof d'enracinement (stRurMaxprec). Pour le reservoir de surface on ne change rien.
    # On MAJ le stRu avec le stock de surface stRuSurf, Hum avec le max de remplissage de surface (RuSurf)
    # Si le StRu avec l'apport d'eau devinet sup au Hum
    # alors on tient compte dans cette augmentation du stock r�silient avec deux cas possible :
    # Si StRu est < � stRurMaxprec
    # alors on ajoute l'eau r�siliente contenue dans l'ancienne zone racinaire en fn
    # de la diff�rence de stock
    # Sinon on a de l'eau r�siliente au maximum de la CC jusqu'� l'ancienne HumPrec,
    # on rempli alors StRu de la diff�rence etre ces deux valeurs puis on fait la MAJ
    # des Dr, StRur, Hum etc...

    # Hypotheses :
    # On a une dynamique de l'eau represente par un remplissage par le haut
    # et une evolution des tailles de reservoirs quand ce remplissage est sup
    # a la quantite maximum de la taille en cours (front d'humectation).
    # Quand on a atteind la taille maximum par remplissage on considere
    # que c'est du drainage.
    # A l'interieur d'un reservoir l'eau est repartie de maniere homogene
    # (peu etre considere valable jusqu'a 2m de profondeur, dixit CB
    # d'apres d'autres sources).

    # 3 representation des reservoirs permettant de simuler 3 reservoirs:
    # 1)ensemble des reservoirs en eau, evoluant en profondeur en fonction
    # du front d'humectation
    # 2) reservoir de surface (taille fixe)ou s'effectue l'evaporation et une part de la
    # transpiration en presence de racines
    # Modif : on a ajoute l'evaporation en dessous du seuil Pf4.2 estime a
    # la moitie de la RU.
    # 3) reservoir contenant les racines, evoluant en fonction du front racinaire
    # REMARQUE : Ces reservoirs se chevauche
    # Au lieu de gerer des profondeurs on gere des stocks d'eau
    # (stRuMax stock d'eau maxi (RU * prof. Max)}

    # eautranspi est reset à chaque itération à 0
    # stRUmax est reset à la valeur ru à chaque itération
    # on ne cast donc pas ces variables sur j


    # reset
    # modif 10/06/2015 Resilience stock eau cas simul pluri en continue
    # lorsque l'on est à l phase 7, on reset les compteurs

    condition = (data["numPhase"][:,:,j] == 7) & (data["changePhase"][:,:,j] == 1)


    data["humPrec"][:,:,j:] = np.where(
        condition,
        np.maximum(data["hum"][:,:,j], data["ruSurf"][:,:,j]),
        data["humPrec"][:,:,j],
    )

    
    print("hum 1",data["hum"][:,:,j])
    data["hum"][:,:,j:] = np.where(
        condition,
        data["ruSurf"][:,:,j],
        data["hum"][:,:,j],
    )
    print("hum 2",data["hum"][:,:,j])


    data["stRurMaxPrec"][:,:,j:] = np.where(
        condition,
        data["stRurMax"][:,:,j],
        data["stRurMaxPrec"][:,:,j],
    )

    data["stRurPrec"][:,:,j:] = np.where(
        condition,
        data["stRur"][:,:,j]/data["stRurMax"][:,:,j],
        data["stRurPrec"][:,:,j],
    )

    data["stRuPrec"][:,:,j:] = np.where(
        condition,
        # data["stRu"][:,:,j] - data["stRurSurf"][:,:,j],
        data["stTot"][:,:,j] - data["stRurSurf"][:,:,j], # essai stTot
        data["stRuPrec"][:,:,j],
    )


    # stRuMax
    # stock d'eau maximal dans la réserve utile ; capacité maximale de la réserve utile
    # redéfinie à chaque boucle comme étant le produit de la réserve utile (mm/m de sol) et 
    # de la profondeur maximale de sol
    # modif 10/06/2015 Resilience stock eau cas simul pluri en continue
    data["stRuMax"][:,:,j:] = (data["ru"][:,:,j] * data["profRu"][:,:,j] / 1000).copy()
    
    # stRuSurfPrec
    # Rempli Res surface
    # on enregistre le stock d'eau de surface précédent 
    data["stRuSurfPrec"][:,:,j] = data["stRuSurf"][:,:,j].copy()
    
    # stRuSurf
    # on met à jour le stock d'eau en surface pour qu'il corresponde au stock de surface incrémenté
    # de la valeur d'eau disponible eauDispo ; 
    # on borne cependant cette valeur à 110% de la réserve utile de surface.
    data["stRuSurf"][:,:,j:] = np.minimum(
        data["stRuSurf"][:,:,j] + data["eauDispo"][:,:,j],
        data["ruSurf"][:,:,j] + data["ruSurf"][:,:,j] / 10
    )

    # eauTranspi
    # quantité d'eau transpirable
    # si le stock de surface avant mise à jour est inférieur à 10% de la réserve utile de surface, 
    # la quantité d'eau transpirable correspond à l'apport d'eau du jour (eauDispo), moins la différence 
    # entre 1/10e de la réserve utile de surface et le stock de surface avant mise à jour, bornée au minimum par 0,
    # (autrement dit, une partie de l'apport d'eau du jour est considérée comme liée au réservoir de surface)
    # sinon la quantité d'eau transpirable est égale à l'apport d'eau du jour (eauDispo)
    data["eauTranspi"][:,:,j:] = np.where(
        data["stRuSurfPrec"][:,:,j] < data["ruSurf"][:,:,j]/10,
        np.maximum(
            0,
            data["eauDispo"][:,:,j] - (data["ruSurf"][:,:,j]/10 - data["stRuSurfPrec"][:,:,j])
            ),
        data["eauDispo"][:,:,j],
    )



    # stRu/stTot étape 1
    # stock d'eau total sur l'ensemble du réservoir
    # on incrémente le stock d'eau total de la quantité d'eau transpirable
    data["stTot"][:,:,j:] = (data["stTot"][:,:,j] + data["eauTranspi"][:,:,j]).copy() ## ok


    # stRuVar
    # modif 10/06/2015 Resilience stock eau cas simul pluri en continue
    # différence entre stock total et stRuPrec (non défini clairement ?), borné au minimum en 0
    data["stRuVar"][:,:,j:] = np.maximum(0, data["stTot"][:,:,j] - data["stRuPrec"][:,:,j])


    condition_1 = (data["stRuVar"][:,:,j] > data["hum"][:,:,j])
    condition_2 = (data["hum"][:,:,j] <= data["stRurMaxPrec"][:,:,j])
    condition_3 = (data["hum"][:,:,j] < data["humPrec"][:,:,j])


    # stRu/stTot étape 1
    # stock d'eau total sur l'ensemble du réservoir
    # si l'évolution du stock total stRuVar est supérieure à la quantité d'eau maximum jusqu'au front d'humectation hum,
    # et que la quantité d'eau jusqu'au front d'humectation est inférieure au stock d'eau racinaire maximal,
    # le stock total est incrémenté de la différence entre l'évolution du stock total et hum,
    # multiplié par le stock racinaire précédent (?)

    data["stTot"][:,:,j:] = np.where(
        condition_1,
        np.where(
            condition_2,
            # data["stRu"][:,:,j] + (data["stRuVar"][:,:,j] - data["hum"][:,:,j]) * data["stRurPrec"][:,:,j],
            data["stTot"][:,:,j] + (data["stRuVar"][:,:,j] - data["hum"][:,:,j]) * data["stRurPrec"][:,:,j],
            np.where(
                condition_3,
                data["stRuVar"][:,:,j],
                # data["stRu"][:,:,j],
                data["stTot"][:,:,j],
            ),
        ),
        # data["stRu"][:,:,j],
        data["stTot"][:,:,j],
    )

    data["stRuPrec"][:,:,j:] = np.where(
        condition_1,
        np.where(
            condition_2,
            np.maximum(0, data["stRuPrec"][:,:,j] - (data["stRuVar"][:,:,j] - data["hum"][:,:,j]) * data["stRurPrec"][:,:,j]),
            np.where(
                condition_3,
                0,
                data["stRuPrec"][:,:,j],
            ),
        ),
        data["stRuPrec"][:,:,j],
    )

    data["stRuVar"][:,:,j:] = np.where(
        condition_1,
        np.where(
            condition_2,
            data["stRuVar"][:,:,j] + (data["stRuVar"][:,:,j] - data["hum"][:,:,j]) * data["stRurPrec"][:,:,j],
            np.where(
                condition_3,
                data["stRuVar"][:,:,j] + data["stRuPrec"][:,:,j],
                data["stRuVar"][:,:,j],
            ),
        ),
        data["stRuVar"][:,:,j],
    )

    # hum
    # front d'humectation mis à jour sur la base du delta maximal de stock d'eau total
    # dans l'intervalle [stRuVar, stRuMax]
    # modif 10/06/2015 Resilience stock eau cas simul pluri en continue
    # modif 27/07/2016 Hum ne peut �tre au dessus de stRu (stocktotal)
    data["hum"][:,:,j:] = np.maximum(data["stRuVar"][:,:,j], data["hum"][:,:,j])
    data["hum"][:,:,j:] = np.minimum(data["stRuMax"][:,:,j], data["hum"][:,:,j])


    condition = (data["stTot"][:,:,j] > data["stRuMax"][:,:,j])

    # essais stTot
    data["dr"][:,:,j] = np.where(
        condition,
        # data["stRu"][:,:,j] - data["stRuMax"][:,:,j],
        data["stTot"][:,:,j] - data["stRuMax"][:,:,j],
        0,
    )

    # essais stTot
    # data["stRu"][:,:,j] = np.where(
    data["stTot"][:,:,j:] = np.where(   
        condition,
        data["stRuMax"][:,:,j],
        # data["stRu"][:,:,j],
        data["stTot"][:,:,j],
    )


    # // avant modif 10/06/2015
    # data["hum"][:,:,j:] = np.maximum(data["hum"][:,:,j], data["stRu"][:,:,j])
    # essais stTot
    data["hum"][:,:,j:] = np.maximum(data["hum"][:,:,j], data["stTot"][:,:,j])
    #! en conflit avec le calcul précédent de hum
    print("hum 5",data["hum"][:,:,j])
    # // Rempli res racines
    data["stRur"][:,:,j:] = np.minimum(data["stRur"][:,:,j] + data["eauTranspi"][:,:,j], data["stRurMax"][:,:,j])
    print("stRur 3",data["stRur"][:,:,j])
    # essais stTot
    # data["stRur"][:,:,j] = np.minimum(data["stRur"][:,:,j], data["stRu"][:,:,j])
    data["stRur"][:,:,j:] = np.minimum(data["stRur"][:,:,j], data["stTot"][:,:,j])
    print("stRur 4",data["stRur"][:,:,j])
    

    return data


def rempliRes_alt(j, data):


   


    # stRuMax
    # stock d'eau maximal dans la réserve utile ; capacité maximale de la réserve utile
    # redéfinie à chaque boucle comme étant le produit de la réserve utile (mm/m de sol) et 
    # de la profondeur maximale de sol
    # modif 10/06/2015 Resilience stock eau cas simul pluri en continue
    data["stRuMax"][:,:,j:] = (data["ru"][:,:,j] * data["profRu"][:,:,j] / 1000).copy()
    
    # stRuSurfPrec
    # Rempli Res surface
    # on enregistre le stock d'eau de surface précédent 
    data["stRuSurfPrec"][:,:,j] = data["stRuSurf"][:,:,j].copy()
    
    # stRuSurf
    # on met à jour le stock d'eau en surface pour qu'il corresponde au stock de surface incrémenté
    # de la valeur d'eau disponible eauDispo ; 
    # on borne cependant cette valeur à 110% de la réserve utile de surface.
    data["stRuSurf"][:,:,j:] = np.minimum(
        data["stRuSurf"][:,:,j] + data["eauDispo"][:,:,j],
        data["ruSurf"][:,:,j] + data["ruSurf"][:,:,j] / 10
    )

    # eauTranspi
    # quantité d'eau transpirable
    # si le stock de surface avant mise à jour est inférieur à 10% de la réserve utile de surface, 
    # la quantité d'eau transpirable correspond à l'apport d'eau du jour (eauDispo), moins la différence 
    # entre 1/10e de la réserve utile de surface et le stock de surface avant mise à jour, bornée au minimum par 0,
    # (autrement dit, une partie de l'apport d'eau du jour est considérée comme liée au réservoir de surface)
    # sinon la quantité d'eau transpirable est égale à l'apport d'eau du jour (eauDispo)
    data["eauTranspi"][:,:,j:] = np.where(
        data["stRuSurfPrec"][:,:,j] < data["ruSurf"][:,:,j]/10,
        np.maximum(
            0,
            data["eauDispo"][:,:,j] - (data["ruSurf"][:,:,j]/10 - data["stRuSurfPrec"][:,:,j])
            ),
        data["eauDispo"][:,:,j],
    )



    # stRu/stTot étape 1
    # stock d'eau total sur l'ensemble du réservoir
    # on incrémente le stock d'eau total de la quantité d'eau transpirable
    data["stTot"][:,:,j:] = (data["stTot"][:,:,j] + data["eauTranspi"][:,:,j]).copy() ## ok




    condition = (data["stTot"][:,:,j] > data["stRuMax"][:,:,j])

    # essais stTot
    data["dr"][:,:,j] = np.where(
        condition,
        # data["stRu"][:,:,j] - data["stRuMax"][:,:,j],
        data["stTot"][:,:,j] - data["stRuMax"][:,:,j],
        0,
    )

    # essais stTot
    # data["stRu"][:,:,j] = np.where(
    data["stTot"][:,:,j:] = np.where(   
        condition,
        data["stRuMax"][:,:,j],
        # data["stRu"][:,:,j],
        data["stTot"][:,:,j],
    )



    data["hum"][:,:,j:] = np.maximum(data["hum"][:,:,j], data["stTot"][:,:,j])

    data["stRur"][:,:,j:] = np.minimum(data["stRur"][:,:,j] + data["eauTranspi"][:,:,j], data["stRurMax"][:,:,j])
    data["stRur"][:,:,j:] = np.minimum(data["stRur"][:,:,j], data["stTot"][:,:,j])




    return data


def EvalFESW(j, data):
    """
    depuis bileau.pas

    Estimation de la fraction d'eau evaporable, rapporte donc au reservoir
    de surface, RuSurf est le stock d'eau maxi disponible pour la plante
    sur ce reservoir
    Modif : on considere que pour l'�vaporation la moitie de cette
    valeur doit etre ajout�e.
    // Parametres
    IN:
    StRusurf : mm
    RuSurf : mm
    OUT:
    fesw : mm
    """

    data["fesw"][:,:,j] = data["stRuSurf"][:,:,j] / (data["ruSurf"][:,:,j] + data["ruSurf"][:,:,j] / 10)

    return data




def EvalKceMc(j, data, paramITK):
    """
    depuis bileau.pas
    
    Trois possibilit�s d'extinction sur l'�vaporation :
    ltr : couverture de la plante
    Mulch : effet couvrant permanent et constant; 100 pas de Mulch, 0 couvert complet bache)
    exp() �quivalent � formule de calcul du ltr mais appliqu� � l'effet couvrant d'un
    mulch couvert de paillis... �volutif    
    """

    # Kce := Mulch/100 * ltr * exp(-coefMc * SurfMc * BiomMc/1000);
    data["kce"][:,:,j] = paramITK["mulch"] / 100 * data["ltr"][:,:,j] * np.exp(-paramITK["coefMc"] * paramITK["surfMc"] * data["biomMc"][:,:,j]/1000)
    
    return data




def DemandeSol(j, data):
    """
    depuis bileau.pas

    Estimation de l'evaporation potentielle du sol, on ne tient pas
    compte d'une variation de l'evaporation en fonction d'une humectation
    differente entre le haut et le bas du reservoir, on a un parametre
    mulch qui peu traduire le phenomene d'auto mulching (defaut : 0.7)
    qui peu aussi traduire un mulch par couverture vegetale ou...
    La reduction de l'evaporation par l'evolution de la couverture
    du sol par la plante est traduit par ltr.

    // Parametres
    IN:
    ETo : mm
    Kce : %
    OUT:
    evapPot : mm
    """
    data["evapPot"][:,:,j:] = (data["ET0"][:,:,j] * data["kce"][:,:,j]).copy()

    return data




def EvapMc(j, data, paramITK):
    """
    depuis bileau.pas

    comme pour FESW on retire du stock la fraction evaporable
    la demande climatique étant réduite é la fraction touchant le sol ltr
    on borne é 0
    """
    # on doit reset FEMcW à chaque cycle ?
    # Var FEMcW : double;

    data["FEMcW"][:,:,j] = np.where(
        data["stockMc"][:,:,j] > 0,
        (paramITK["humSatMc"] * data["biomMc"][:,:,j] * 0.001) / data["stockMc"][:,:,j],
        data["FEMcW"][:,:,j],
    )

    data["stockMc"][:,:,j:] = np.maximum(
        0,
        data["stockMc"][:,:,j] - data["ltr"][:,:,j] * data["ET0"][:,:,j] * data["FEMcW"][:,:,j]**2,
    )

    return data




def EvapRuSurf(j, data):
    """
    depuis bileau.pas 

    Estimation de l'evaporation relle, rapporte a la fraction d'eau evaporable
    // Parametres
    IN:
    fesw : mm
    evapPot : mm
    stRuSurf : mm
    OUT:
    evap : mm
    """

    data["evap"][:,:,j:] = np.minimum(data["evapPot"][:,:,j] * data["fesw"][:,:,j]**2, data["stRuSurf"][:,:,j])

    return data





def EvalFTSW(j, data):
    """
    depuis bileau.pas 

    Estimation de la fraction d'eau transpirable, rapporte donc au reservoir
    contenant les racines
    // Parametres
    IN:
    RuRac : mm
    StockRac : mm
    OUT:
    ftsw : mm
    """

    data["ftsw"][:,:,j:] = np.where(
        data["stRurMax"][:,:,j] > 0,
        data["stRur"][:,:,j] / data["stRurMax"][:,:,j],
        0,
    )

    return data




def DemandePlante(j, data):
    # d'près bileau.pas
    # TrPot := Kcp * ETo;
    # attention, séparation de ETp et ET0 dans les formules
    data["trPot"][:,:,j:] = (data["kcp"][:,:,j] * data["ET0"][:,:,j]).copy()
    
    return data




def EvalKcTot(j, data):
    # d'après bileau.pas
    # added a condition on 19/08/22 to match SARRA-H original behavior
    data["kcTot"][:,:,j:] = np.where(
        data["kcp"][:,:,j] == 0.0,
        data["kce"][:,:,j],
        data["kce"][:,:,j] + data["kcp"][:,:,j],
    )

    return data


def CstrPFactor(j, data, paramVariete):

    # d'après bileau.pas

    data["pFact"][:,:,j:] = paramVariete["PFactor"] + 0.04 * (5 - np.maximum(data["kcp"][:,:,j], 1) * data["ET0"][:,:,j])
    data["pFact"][:,:,j:] = np.minimum(np.maximum(0.1, data["pFact"][:,:,j]), 0.8)

    data["cstr"][:,:,j:] = np.minimum((data["ftsw"][:,:,j] / (1 - data["pFact"][:,:,j])), 1)
    data["cstr"][:,:,j:] = np.maximum(0, data["cstr"][:,:,j])

    return data




def EvalTranspi(j, data):
    # d'après bileau.pas
    
    data["tr"][:,:,j:] = (data["trPot"][:,:,j] * data["cstr"][:,:,j]).copy()
    return data




def ConsoResSep(j, data):
    """
    d'après bileau.pas

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

    # part transpirable sur le reservoir de surface
    data["trSurf"][:,:,j:] = np.maximum(0, data["stRuSurf"][:,:,j] - data["ruSurf"][:,:,j] / 10)

    # qte d'eau evapore a consommer sur le reservoir de surface
    data["stRuSurf"][:,:,j:] = np.maximum(0, data["stRuSurf"][:,:,j] - data["evap"][:,:,j])
    print("stRuSurf 3",data["stRuSurf"][:,:,j])

    # qte d'eau evapore a retirer sur la part transpirable
    data["consoRur"][:,:,j:] = np.where(
        data["evap"][:,:,j] > data["trSurf"][:,:,j],
        data["trSurf"][:,:,j],
        data["evap"][:,:,j],
    )

    # data["stRu"][:,:,j:] = np.maximum(0, data["stRu"][:,:,j] - data["consoRur"][:,:,j])
    # essais stTot
    data["stTot"][:,:,j:] = np.maximum(0, data["stTot"][:,:,j] - data["consoRur"][:,:,j])

    #  fraction d'eau evapore sur la part transpirable qd les racines sont moins
    #  profondes que le reservoir de surface, mise a jour des stocks transpirables
    data["consoRur"][:,:,j:] = np.where(
        data["stRurMax"][:,:,j] < data["ruSurf"][:,:,j],
        data["evap"][:,:,j] * data["stRur"][:,:,j] / data["ruSurf"][:,:,j],
        data["consoRur"][:,:,j],
    )

    data["stRur"][:,:,j:] = np.maximum(0, data["stRur"][:,:,j] - data["consoRur"][:,:,j])
    print("stRur 5",data["stRur"][:,:,j])

    # // reajustement de la qte transpirable considerant que l'evap a eu lieu avant
    # // mise a jour des stocks transpirables  
    data["tr"][:,:,j:] = np.where(
        data["tr"][:,:,j] > data["stRur"][:,:,j],
        np.maximum(data["stRur"][:,:,j] - data["tr"][:,:,j], 0),
        data["tr"][:,:,j],
    )

    data["stRuSurf"][:,:,j:] = np.where(
        data["stRur"][:,:,j] > 0,
        np.maximum(data["stRuSurf"][:,:,j] - (data["tr"][:,:,j] * np.minimum(data["trSurf"][:,:,j]/data["stRur"][:,:,j], 1)), 0),
        data["stRuSurf"][:,:,j],
    )
    print("stRuSurf 4",data["stRuSurf"][:,:,j])


    data["stRur"][:,:,j:] = np.maximum(0, data["stRur"][:,:,j] - data["tr"][:,:,j])
    print("stRur 6",data["stRur"][:,:,j])
    # data["stRu"][:,:,j:] = np.maximum(0, data["stRu"][:,:,j] - data["tr"][:,:,j])
    # essais stTot
    data["stTot"][:,:,j:] = np.maximum(0, data["stTot"][:,:,j] - data["tr"][:,:,j]) ## ok
    data["etr"][:,:,j:] = (data["tr"][:,:,j] + data["evap"][:,:,j]).copy()
    data["etm"][:,:,j:] = (data["trPot"][:,:,j] + data["evapPot"][:,:,j]).copy()

    return data