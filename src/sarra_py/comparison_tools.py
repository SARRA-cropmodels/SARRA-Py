from matplotlib import pyplot as plt
import pandas as pd
import numpy as np

def get_var_correspondance():
    var_correspondance = {
        'DegresDuJour':"ddj",
        'Lai':"lai",
        'FTSW':"ftsw",
        'Cstr':"cstr",
        'Eto':"ET0",
        'ETM':"etm",
        'ETR':"etr",
        'Sla':"sla",
        'Assim':"assim",
        # 'DayLength',
        'Par':'par',
        # 'RgCalc',
        # 'VDPCalc',
        'TMoyCalc':"tpMoy",
        # 'HMoyCalc',
        'EauDispo':'eauDispo',
        'StockSurface':"stRuSurf",
        'StockRac':"stRur",
        'RURac':'stRurMax',
        'Kcp':'kcp',
        'Kce':"kce",
        'EvapPot':'evapPot',
        'Evap':"evap",
        'TrPot':"trPot",
        'Tr':"tr",
        'Lr':'lr',
        'Dr':'dr',
        'SumDegresDay':"sdj",
        'BiomasseTotale':"biomasseTotale",
        'BiomasseAerienne':'biomasseAerienne',
        'BiomasseFeuilles':"biomasseFeuille",
        'BiomasseTiges':"biomasseTige",
        'BiomasseVegetative':"biomasseVegetative",
        'BiomasseRacinaire':"biomasseRacinaire",
        'Rdt':"rdt",
        'VitesseRacinaire':"vRac",
        'FESW':"fesw",
        'Kc':"kcTot",
        'Ltr':'ltr',
        'DRespMaint':'respMaint',
        'DBiomTot':"deltaBiomasseTotale",
        'DRdtPot':"dRdtPot", 
        'Reallocation':'reallocation',
        'RdtPot':'rdtPot',
        # 'RayExtra',
        # 'SumDDPhasePrec',
        # 'SeuilTemp',
        # 'TMinMoy',
        # 'TMaxMoy',
        # 'FtswMoy',
        'IrrigTotDay':'irrigTotDay',
        'Conversion':'conv',
        'StockTotal':'stTot',
        'BiomMc':'biomMc',
        'StockMc':'stockMc',
        'LitFeuilles':"litFeuilles",
        'LitTiges':"litTiges",
        'FeuillesUp':"feuillesUp",
        'TigesUp':"tigesUp",
        'Hum':"hum",
        #'EToCO2',
    }

    return var_correspondance

def graph_comparison(var_gt, var_sim, data, df_weather, df_gt):

    plt.rcParams["figure.figsize"] = [7.50, 3.50]
    plt.rcParams["figure.autolayout"] = True

    ax1 = plt.subplot()
    l1, = ax1.plot(df_weather["Jour"], data["numPhase"][0,0,:], color='black', label="sim")

    ax2 = ax1.twinx()
    l2, = ax2.plot(df_weather["Jour"], data[var_sim][0,0,:], color='red', label=var_sim+" (sim)")
    l3, = ax2.plot(df_gt["Jour"], df_gt[var_gt], color='orange', label=var_gt+" (sarrah)")

    # plt.plot(df_weather["Jour"], data["numPhase"][0,0,:], label="numPhase", alpha=0.5)
    # plt.plot(df_weather["Jour"], data[var_sim][0,0,:], color='red', label=var_sim+" (sim)")
    # plt.plot(df_gt["Jour"], df_gt[var_gt], color='orange', label=var_gt+" (sarrah)")
    
    plt.legend([l1, l2, l3], ["numPhase",var_sim+" (sim)", var_gt+" (sarrah)"])
    plt.legend()
    plt.xticks(rotation=45)
    plt.show()


def compute_earliest_diff(var_gt, var_sim, data, df_weather, df_gt, tol=10E-6):
    try:
        df_gt_2 = df_gt
        df_gt_2 = df_gt_2.merge(pd.DataFrame({"Jour":df_weather["Jour"],var_sim:data[var_sim][0,0,:]}), left_on="Jour", right_on="Jour")
        df_gt_2["delta"] = np.abs(df_gt_2[var_sim] - df_gt_2[var_gt])
        df_gt_2["signif"] = False
        df_gt_2["signif"] = df_gt_2.apply(lambda x: x["delta"]>tol, axis=1)
        if np.nansum(df_gt_2["signif"]) == 0.0:
            earliest=datetime.date(1990,1,1)
        else:
            earliest = df_gt_2.loc[df_gt_2["signif"]==True,"Jour"].values[0]
        meandiff = np.nanmean(df_gt_2["delta"])
    except:
        earliest,meandiff = np.nan,np.nan
    return earliest,meandiff