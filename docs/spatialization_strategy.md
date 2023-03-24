# Spatialization strategy

SARRA-Py is a spatialized version of the crop model SARRA-H, developed to estimate the impact of climate scenarios on annual crops. The simulation is performed on a daily time step, with a simple dynamic hydrological balance model that assumes crop performance is a function of the accumulated hydrological constraints during the crop's growth cycle.

The spatialization strategy used in SARRA-Py involves storing all model variables in georeferenced xarrays. Xarrays are a powerful data structure for working with geospatial arrays, as they allow for computations to be performed on regular, georeferenced grids instead of single points or non-georeferenced arrays. This enables the output of maps, making the model suitable for regional scale analyses which can provide valuable insights into the simulation results.

The advantage of the spatialization strategy used in SARRA-Py is that it allows users to perform simulations across a territory, instead of just at one point. This means that the model can be used to perform spatial aggregation of the estimated values, such as drought index or potential yield. This is particularly useful for regional-scale analyses and can provide valuable information for early warning systems for food security issues, as well as for evaluating the potential impacts of climate change on crop systems.

The spatialization of the simulation in SARRA-Py has several benefits for users compared to a non-spatialized version of the model. It enables the performance of simulations across a territory, making it possible to perform spatial aggregations of estimated drought indices, potential yields, and other relevant metrics.

## Simulation logic

The whole simulation results and intermediate steps are stored in a xarray with dimensions (d, x, y), where d is the index of the Julian day and x,y are the spatial coordinates. On each day, the simulation performs a series of operations using variables from both the current day and the previous day, updating the slice in the xarray.

The simulation in SARRA-Py works by updating the xarray of variables on a daily basis. For each day, the model performs a series of operations using the variables from the current and previous day, and updates the corresponding slice in the xarray. The whole simulation and its intermediate steps are stored in a 3D xarray, with dimensions for the Julian day, and the x and y spatial coordinates.

## Array resolution

The initial resolution of the arrays is defined by the resolution of satellite rainfall estimation products, which serve as an important input to the model in computing the water balance.

In SARRA-Py, the resolution of the xarrays is defined by the resolution of satellite rainfall estimation products, which serve as an important input for the model's calculation of water balance. By using these products as the resolution, the model can accurately capture the impact of rainfall on crop yield, which is one of the main drivers for crop performance.

## Performance 

However, it is worth noting that xarrays can be computationally slow, so it may be necessary to use tools such as Dask to increase performance. Despite this, the spatialization of the simulation in SARRA-Py provides a powerful tool for users, and the package is provided with notebook examples to illustrate its use.