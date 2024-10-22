from .bilan_pheno import *
from .bilan_carbo import *
from .bilan_hydro import *
from .data_preparation import *

from tqdm import tqdm as tqdm


def run_model(paramVariete, paramITK, paramTypeSol, data, duration):
    """
    This is the functions list adapted from the procedures of the SARRA-H v42 model.

    Args:
        paramVariete (_type_): _description_
        paramITK (_type_): _description_
        paramTypeSol (_type_): _description_
        data (_type_): _description_
        duration (_type_): _description_

    Returns:
        _type_: _description_
    """
    
    for j in tqdm(range(duration)):

        # updating phenological stages
        data = EvalPhenoSarrahV3(j, data, paramITK, paramVariete)

        # sum of thermal sime is being computed from the day the crop is sown, including the day of sowing
        data = calculate_sum_of_thermal_time(j, data)

        ### water balance
        data = compute_irrigation_state(j, data, paramITK)

        # sums rainfall and irrigation history
        data = compute_total_available_water(j, data)

        # can be conditioned to the presence of mulch
        data = fill_mulch(j, data, paramITK)
        

        data = compute_runoff(j, data)
        data = EvolRurCstr2(j, data, paramITK) 
        
        # computation of filling of the tanks is done after other computations related to water,
        # as we consider filling is taken into consideration at the end of the day
        data = fill_tanks(j, data) 

        # transpiration
        # estimation of the fraction of evaporable soil water (fesw)
        data = compute_soil_evaporation(j, data, paramITK)


        data = estimate_FEMcW_and_update_mulch_water_stock(j, data, paramITK)
        
        
        data = compute_transpiration(j, data, paramVariete)
        
        # water consumption
        data = ConsoResSep(j, data) # ***bileau***; exmodules 1 & 2 # trad O
        
        # # phenologie
        data = update_root_growth_speed(j, data, paramVariete) 

        # # bilan carbone
        data = estimate_ltr(j, data, paramVariete)
        data = estimate_KAssim(j, data, paramVariete)
        data = estimate_conv(j,data,paramVariete)

        # adjusting for sowing densité, in
        data = adjust_for_sowing_density(j, data, paramVariete, direction = "in") # ***bilancarbonsarra*** # trad OK
        
        data = update_assimPot(j, data, paramVariete, paramITK)
        data = update_assim(j, data)

        data = calculate_maintainance_respiration(j, data, paramVariete)
        data = update_total_biomass(j, data, paramVariete, paramITK)


        data = update_total_biomass_stade_ip(j, data)
        data = update_total_biomass_at_flowering_stage(j, data)
        data = update_potential_yield(j, data, paramVariete)
        data = update_potential_yield_delta(j, data, paramVariete)

        data = update_aboveground_biomass(j, data, paramVariete)

        data = estimate_reallocation(j, data, paramVariete)

        data = update_root_biomass(j, data)
        data = EvalFeuilleTigeSarrahV4(j, data, paramVariete)
        data = update_vegetative_biomass(j, data)

        data = calculate_canopy_specific_leaf_area(j, data, paramVariete)
        data = calculate_leaf_area_index(j, data)
        
        data = update_yield_during_filling_phase(j, data) 
        
        #phenologie
        data = update_photoperiodism(j, data, paramVariete)
        
        # # bilan carbone
        data = MortaliteSarraV3(j, data, paramITK, paramVariete)
        
        
        data = adjust_for_sowing_density(j, data, paramVariete, direction="out")
        
        
        # data = BiomMcUBTSV3(j, data, paramITK) # ***bilancarbonsarra***, exmodules 2
        # data = MAJBiomMcSV3(data) # ***bilancarbonsarra***, exmodules 2

        data = estimate_critical_nitrogen_concentration(j, data)


    return data



def run_waterbalance_model(paramVariete, paramITK, paramTypeSol, data, duration):
    """
    This is the functions list adapted from the procedures of the SARRA-H v42 model.

    Args:
        paramVariete (_type_): _description_
        paramITK (_type_): _description_
        paramTypeSol (_type_): _description_
        data (_type_): _description_
        duration (_type_): _description_

    Returns:
        _type_: _description_
    """
    
    for j in tqdm(range(duration)):

        # calculating daily thermal time, independently of sowing date
        data = calculate_daily_thermal_time(j, data, paramVariete)

        # updating phenological stages
        data = EvalPhenoSarrahV3(j, data, paramITK, paramVariete)

        # sum of thermal sime is being computed from the day the crop is sown, including the day of sowing
        data = calculate_sum_of_thermal_time(j, data)

        ### water balance
        # computing irrigation state
        data = compute_irrigation_state(j, data, paramITK)

        # sums rainfall and irrigation history
        data = compute_total_available_water(j, data)

        # filling the mulch
        data = fill_mulch(j, data, paramITK)

        # computing runoff
        data = compute_runoff(j, data)

        # computing evolution of tanks related to root growth
        data = EvolRurCstr2(j, data, paramITK) 
        
        # computation of filling of the tanks is done after other computations related to water,
        # as we consider filling is taken into consideration at the end of the day
        data = fill_tanks(j, data) 

        # evaporation
        data = compute_soil_evaporation(j, data, paramITK)

        #estimate water evaporated from the mulch and update mulch water stock
        data = estimate_FEMcW_and_update_mulch_water_stock(j, data, paramITK)

        # transpiration
        data = compute_transpiration(j, data, paramVariete)
        
        # water consumption
        data = ConsoResSep(j, data) # ***bileau***; exmodules 1 & 2 # trad O
        
        # # phenologie
        data = update_root_growth_speed(j, data, paramVariete) 

        # # bilan carbone
        data = estimate_ltr(j, data, paramVariete)
        data = estimate_KAssim(j, data, paramVariete)
        data = estimate_conv(j,data,paramVariete)


    return data