# Model formalisms

As for the rest of the SARRA family of models, SARRA-Py is a crop simulation model that uses three main processes in a daily loop: 

1. Water balance : estimation of evapotranspiration, water stress index, via three reservoirs

2. Carbon balance : based on the concept of "big leaf", conversion of solar energy into assimilates under water stress constraints, and repartition into biomass

3. Phenology : evolution of phenological stages (emergence, vegetative stage, flowering, maturation) and associated processes (germination, juvenile mortality, distribution modes of biomasses, etc.).

## Water balance

The SARRA-Py water balance process considers soil as a collection of reservoirs of varying sizes: surface, deep, and a dynamic root reservoir. Each reservoir is an entity that is homogeneous in terms of simulated processes or variables that describe its properties such as infiltration/surface runoff, drainage, storage capacity, and water consumption.

The flux is simulated by filling the reservoir to its maximum capacity, traditionally the field capacity, except for groundwater phenomena where it is filled to saturation. Beyond that, the water overflows to the next reservoir, downward vertical flux. The water that overflows from the last reservoir is considered drainage. The capillary rise process is not simulated.

Three representations of the reservoirs are used to estimate available water for evaporation, transpiration, and water storage processes :

* a fixed-size surface reservoir, that manages the soil evaporation process,
* a deep reservoir, on which moisture front is simulated ; this allows: 1) to limit the rooting depth to the moisture front, 2) to store water not yet accessible by roots, 3) to block rooting in the case of hard soils,
* and a root reservoir that evolves based on the rooting speed of roots during their development phases and simulates water availability for plant transpiration.

The overall water balance equation is:

`stock(d+1) = stock(d) + (rain + irrigation) - runoff - drainage - (tr + evap)`

where stock is the water stored in the reservoirs, runoff is a function of water input and soil texture, drainage is overflow from the deep reservoir, tr is transpiration, and evap is evaporation.

The size of the root reservoir prospected by roots evolves based on the daily rooting speed defined for each phenological phase and can be blocked by the moisture front or reduced in case of strong hydric stress.

## Carbon balance

The carbon balance in SARRA-Py is based on a big-leaf approach. The photosynthetically active radiation (PAR) to be transformed into assimilates based on photosynthetic activity is estimated from 1) calculating the intercepted fraction of PAR (deduced via the Beer law from the plot-level leaf area index (LAI) and leaf geometry (factor kdf)), and 2) applying a conversion rate.

The conversion rate is considered constant throughout the cycle, and is higher than commonly given since it aims at representing all produced assimilates, whereas conversion rates traditionally used in other models only take into account the increase in aerial biomass, without root biomass or maintenance respiration. This photosynthetic activity is constrained constrained by the availability of water and nutrients, representing processes such as stomatal regulation.

Assimilates are then allocated between biomasses following rules that vary depending on the phases :

* A portion of the assimilates is consumed without producing biomass for the maintenance of living tissues, known as maintenance respiration.

* From emergence to flowering, biomass is split into root biomass and aerial biomass, which is further divided into leaf and stem biomass using allometric relationships.

* After flowering, the available assimilates allow for seed filling.

The overall equation of the carbon balance is defined as:

`total biomass (d+1) = biomass (d) + assimilates - maintenance respiration`

`total biomass = root biomass + leaf biomass + stem biomass + grain biomass`

The value of LAI, being the ratio of the limb surface to the ground surface, can then be updated from the leaf biomass based on the specific leaf area (SLA). SLA is considered to be decreasing with the age of the leaf, due to its thickening. Other factors contribute to leaf thickening, including exposure levels to radiation and competition for assimilates Additionally, its dynamics vary depending on plant type (monocotyledons and dicotyledons). The leaf surface area is nonetheless a genetic characteristic that can be defined by minimum and maximum values. In this model, minimum and maximum values, as well as linear decrease rate of SLA are taken into consideration.

Finally, the grain yield potential is defined as a fixed fraction of the aerial biomass (genetic potential). It can be diminished by various processes during the reproductive phase, water stress (which result in reduced biomass during the critical phase). The grain yield is mainly dependent on the grain filling phase, where water is the main constraint and the grain demand is the highest and considered a priority. The grain yield is calculated based on the temperature of the day and the defined temperature sum for this phase, multiplied by the grain yield potential. For species with continuous flowering, the grain yield is calculated daily and can be affected by the flowering process.

The influence of seeding density is also taken into account, where a linear relationship is applied for low densities and an asymptotic relationship for high densities. The carbon balance calculations for biomass, yield and LAI are simulated daily with an optimal density and converted from the actual density to the optimal density using the asymptotic relationship.

## Phenology 

Phenology is the study of the growth and development of plants and it is a crucial component of SARRA-Py. The crop growth cycle is traditionally divided into four phases: juvenile vegetative phase (BVP), photoperiod-sensitive phase (PSP), reproductive phase (RPR), and maturation phase (Matu). SARRA-Py divides these phases into seven stages to optimize calculation and control methods. These stages are determined by the sum of degree days and the length of the day, and are defined by different thresholds (temperature, PP function). The PSP phase depends on the photoperiod sensitivity of the variety, which varies with the latitude and sowing date. The RPR and maturation phases are the most sensitive to constraints and have a significant impact on yield in cereal crops. The degree days are calculated based on the temperature range between the base temperature, lethal temperature, and optimum temperatures for plant development.