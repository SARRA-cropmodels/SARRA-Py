from os import listdir
from os.path import isfile, join
import pandas as pd
import datetime
import rasterio
import os
import rioxarray
from tqdm import tqdm as tqdm
import numpy as np
import yaml
import xarray as xr
import astral
from astral.sun import sun
from astral import LocationInfo





def build_rainfall_files_df(rainfall_path, date_start, duration):
    """
    This function builds a dataframe containing the list of rainfall files
    from the provided path, and the given date_start and duration.
    
    Helper function used in get_grid_size() and load_TAMSAT_data().

    Args:
        rainfall_path (_type_): _description_

    Returns:
        _type_: _description_
    """
    #rainfall_files = [f for f in listdir(rainfall_path) if isfile(join(rainfall_path, f))]
    # version that should be quicker
    rainfall_files = [f for f in listdir(rainfall_path)]# if isfile(join(rainfall_path, f))]
    rainfall_files_df = pd.DataFrame({"filename":rainfall_files}).sort_values("filename").reset_index(drop=True)

    rainfall_files_df["date"] = rainfall_files_df.apply(
        lambda x: datetime.date(
            int(x["filename"].replace(".tif","").split("_")[-3]),
            int(x["filename"].replace(".tif","").split("_")[-2]),
            int(x["filename"].replace(".tif","").split("_")[-1]),
        ),
        axis=1,
    )

    rainfall_files_df = rainfall_files_df[(rainfall_files_df["date"]>=date_start) & (rainfall_files_df["date"]<date_start+datetime.timedelta(days=duration))].reset_index(drop=True)

    return rainfall_files_df
 




def get_grid_size(rainfall_path, date_start, duration):
    """
    This function loads the list of rainfall files corresponding to the given
    date_start and duration, loads the first rainfall file, and returns its grid
    size, as dimensions of the rainfall grid define the output resolution of the
    model.

    Args:
        TAMSAT_path (_type_): _description_
        date_start (_type_): _description_
        duration (_type_): _description_

    Returns:
        _type_: _description_
    """    

    rainfall_files_df = build_rainfall_files_df(rainfall_path, date_start, duration)

    # checking coherence between date_start and duration and available rainfall data
    if rainfall_files_df["date"].iloc[-1] != date_start+datetime.timedelta(days=duration-1) :
        raise ValueError("The date range may not be covered by the available rainfall data ; please check rainfall entry files.")

    # loading the first rainfall file to get the grid size
    src = rasterio.open(os.path.join(rainfall_path,rainfall_files_df.loc[0,"filename"]))
    array = src.read(1)
    grid_width = array.shape[0]
    grid_height = array.shape[1]

    return grid_width, grid_height




def load_TAMSAT_data(data, TAMSAT_path, date_start, duration):
    """
    This function loops over the rainfall raster files, and loads them into a
    xarray DataArray, which is then added to the rain data dictionary. It is
    tailored to the TAMSAT rainfall data files, hence its name.

    Args:
        data (_type_): _description_
        TAMSAT_path (_type_): _description_
        date_start (_type_): _description_
        duration (_type_): _description_

    Returns:
        _type_: _description_
    """

    TAMSAT_files_df = build_rainfall_files_df(TAMSAT_path, date_start, duration)

    for i in range(len(TAMSAT_files_df)):

        dataarray = rioxarray.open_rasterio(os.path.join(TAMSAT_path,TAMSAT_files_df.loc[i,"filename"]))
        dataarray = dataarray.squeeze("band").drop_vars(["band", "spatial_ref"])
        dataarray.attrs = {}

        try:
            dataarray_full = xr.concat([dataarray_full, dataarray],"time")
        except:
            dataarray_full = dataarray

    dataarray_full.rio.write_crs(4326,inplace=True)
    data["rain"] = dataarray_full
    data["rain"].attrs = {"units":"mm", "long_name":"rainfall"}

    return data




def load_TAMSAT_data_fast(data, rainfall_data_path, date_start, duration):
    """
    This function loops over the rainfall raster files, and loads them into a
    xarray DataArray, which is then added to the rain data dictionary. It is
    tailored to the TAMSAT rainfall data files, hence its name.

    Args:
        data (_type_): _description_
        TAMSAT_path (_type_): _description_
        date_start (_type_): _description_
        duration (_type_): _description_

    Returns:
        _type_: _description_
    """

    rainfall_data_path_df = build_rainfall_files_df(rainfall_data_path, date_start, duration)
    dataarray_full = xr.open_mfdataset([os.path.join(rainfall_data_path,rainfall_data_path_df.loc[i,"filename"]) for i in range(len(rainfall_data_path_df))], concat_dim="time", combine="nested", chunks={"x":100,"y":100})
    dataarray_full = dataarray_full.squeeze("band").drop_vars(["band"])
    dataarray_full.rio.write_crs(4326,inplace=True)
    data["rain"] = dataarray_full["band_data"]

    return data





def load_AgERA5_data(data, AgERA5_data_path, date_start, duration):
    """
    This function loops over the AgERA5 raster files, and loads them into 
    xarray DataArray, which are then added to the data dictionary.

    Args:
        data (_type_): _description_
        AgERA5_data_path (_type_): _description_
        date_start (_type_): _description_
        duration (_type_): _description_

    Returns:
        _type_: _description_
    """
    # TODO : make the file listing error-proof regarding the structure of the folder and the file extensions

    # getting list of variables
    AgERA5_variables = [path.split("/")[-1] for path in [x[0] for x in os.walk(AgERA5_data_path)][1:]]

    # building a dictionary of dataframes containing the list of files for each variable
    AgERA5_files_df_collection = {}

    for variable in AgERA5_variables:
        #AgERA5_files = [f for f in listdir(os.path.join(AgERA5_data_path,variable)) if isfile(join(os.path.join(AgERA5_data_path,variable), f))]
        # alternate version that should be quicker
        AgERA5_files = [f for f in listdir(os.path.join(AgERA5_data_path,variable))]
        AgERA5_files_df_collection[variable] = pd.DataFrame({"filename":AgERA5_files})

        AgERA5_files_df_collection[variable]["date"] = AgERA5_files_df_collection[variable].apply(
            lambda x: datetime.date(
                int(x["filename"].replace(".tif","").split("_")[-3]),
                int(x["filename"].replace(".tif","").split("_")[-2]),
                int(x["filename"].replace(".tif","").split("_")[-1]),
            ),
            axis=1,
        )


    # building a dictionary of correspondance between AgERA5 variables and SARRA variables
    AgERA5_SARRA_correspondance = {
        '10m_wind_speed_24_hour_mean':None,
        '2m_temperature_24_hour_maximum':None,
        '2m_temperature_24_hour_mean':'tpMoy',
        '2m_temperature_24_hour_minimum':None,
        'ET0Hargeaves':'ET0',
        'solar_radiation_flux_daily':'rg',
        'vapour_pressure_24_hour_mean':None,
    }

    # loading the data
    for variable in tqdm(AgERA5_variables) :
        print(variable)
        if AgERA5_SARRA_correspondance[variable] != None :

            try:
                del dataarray_full
            except:
                pass
            
            for i in range(duration) :
                dataarray = rioxarray.open_rasterio(os.path.join(AgERA5_data_path,variable,AgERA5_files_df_collection[variable].loc[i,"filename"]))
                dataarray = dataarray.rio.reproject_match(data, nodata=np.nan)
                dataarray = dataarray.squeeze("band").drop_vars(["band"])
                # TODO: add dataarray.attrs = {} to precise units and long_name

                try:
                    dataarray_full = xr.concat([dataarray_full, dataarray],"time")
                except:
                    dataarray_full = dataarray

            # storing the variable in the data dictionary
            data[AgERA5_SARRA_correspondance[variable]] = dataarray_full
            
    # unit conversion for solar radiation (kJ/m2 as provided by AgERA5 to MJ/m2/day)
    data["rg"] = data["rg"]/1000
    
    return data





def load_AgERA5_data_fast_dask(data, AgERA5_data_path, date_start, duration):
    """
    This function loops over the AgERA5 raster files, and loads them into 
    xarray DataArray, which are then added to the data dictionary.

    Args:
        data (_type_): _description_
        AgERA5_data_path (_type_): _description_
        date_start (_type_): _description_
        duration (_type_): _description_

    Returns:
        _type_: _description_
    """
    # TODO : make the file listing error-proof regarding the structure of the folder and the file extensions

    # getting list of variables
    AgERA5_variables = [path.split("/")[-1] for path in [x[0] for x in os.walk(AgERA5_data_path)][1:]]

    # building a dictionary of dataframes containing the list of files for each variable
    AgERA5_files_df_collection = {}

    for variable in AgERA5_variables:
        #AgERA5_files = [f for f in listdir(os.path.join(AgERA5_data_path,variable)) if isfile(join(os.path.join(AgERA5_data_path,variable), f))]
        # alternate version that should be quicker
        AgERA5_files = [f for f in listdir(os.path.join(AgERA5_data_path,variable))]
        AgERA5_files_df_collection[variable] = pd.DataFrame({"filename":AgERA5_files})

        AgERA5_files_df_collection[variable]["date"] = AgERA5_files_df_collection[variable].apply(
            lambda x: datetime.date(
                int(x["filename"].replace(".tif","").split("_")[-3]),
                int(x["filename"].replace(".tif","").split("_")[-2]),
                int(x["filename"].replace(".tif","").split("_")[-1]),
            ),
            axis=1,
        )

        AgERA5_files_df_collection[variable] = AgERA5_files_df_collection[variable][(AgERA5_files_df_collection[variable]["date"]>=date_start) & (AgERA5_files_df_collection[variable]["date"]<date_start+datetime.timedelta(days=duration))].reset_index(drop=True)

    # building a dictionary of correspondance between AgERA5 variables and SARRA variables
    AgERA5_SARRA_correspondance = {
        '10m_wind_speed_24_hour_mean':None,
        '2m_temperature_24_hour_maximum':None,
        '2m_temperature_24_hour_mean':'tpMoy',
        '2m_temperature_24_hour_minimum':None,
        'ET0Hargeaves':'ET0',
        'solar_radiation_flux_daily':'rg',
        'vapour_pressure_24_hour_mean':None,
    }

    # loading the data
    for variable in tqdm(AgERA5_variables) :
        if AgERA5_SARRA_correspondance[variable] != None :

            try:
                del dataarray_full
            except:
                pass
            
            # for i in range(duration) :
            #     dataarray = rioxarray.open_rasterio(os.path.join(AgERA5_data_path,variable,AgERA5_files_df_collection[variable].loc[i,"filename"]))
            #     dataarray = dataarray.rio.reproject_match(data, nodata=np.nan)
            #     dataarray = dataarray.squeeze("band").drop_vars(["band"])
            #     # TODO: add dataarray.attrs = {} to precise units and long_name

            #     try:
            #         dataarray_full = xr.concat([dataarray_full, dataarray],"time")
            #     except:
            #         dataarray_full = dataarray


            dataarray_full = xr.open_mfdataset([os.path.join(AgERA5_data_path,variable,AgERA5_files_df_collection[variable].loc[i,"filename"]) for i in range(len(AgERA5_files_df_collection[variable]))], concat_dim="time", combine="nested", chunks={"x":1000,"y":1000})
            dataarray_full = dataarray_full.squeeze("band").drop_vars(["band"])
            dataarray_full = dataarray_full.rio.reproject_match(data, nodata=np.nan)

            
            dataarray_full.rio.write_crs(4326,inplace=True)
            
            
            data[AgERA5_SARRA_correspondance[variable]] = dataarray_full["band_data"]

            
    # unit conversion for solar radiation (kJ/m2 as provided by AgERA5 to MJ/m2/day)
    data["rg"] = data["rg"]/1000
    
    return data









def load_paramVariete(file_paramVariete) :
    """
    This function loads the parameters of the variety from the yaml file.

    Args:
        file_paramVariete (_type_): _description_

    Raises:
        exception: _description_

    Returns:
        _type_: _description_
    """
    with open(os.path.join('../data/params/variety/',file_paramVariete), 'r') as stream:
        paramVariete = yaml.safe_load(stream)
    if paramVariete["feuilAeroBase"] == 0.1 :
        raise Exception()
    return paramVariete





def load_paramITK(file_paramITK):
    """
    This function loads the ITK parameters from the yaml file.

    Args:
        file_paramITK (_type_): _description_

    Returns:
        _type_: _description_
    """
    with open(os.path.join('../data/params/itk/',file_paramITK), 'r') as stream:
        paramITK = yaml.safe_load(stream)
    paramITK["DateSemis"] = datetime.datetime.strptime(paramITK["DateSemis"], "%Y-%m-%d").date()
    return paramITK





def load_paramTypeSol(file_paramTypeSol):
    """
    This function loads the soil parameters from the yaml file.

    Args:
        file_paramTypeSol (_type_): _description_

    Returns:
        _type_: _description_
    """
    with open(os.path.join('../data/params/soil/',file_paramTypeSol), 'r') as stream:
        paramTypeSol = yaml.safe_load(stream)     
    return paramTypeSol





def load_YAML_parameters(file_paramVariete, file_paramITK, file_paramTypeSol):
    """
    This function loads the parameters from the yaml files.
    It is a wrapper for the three functions above.

    Args:
        file_paramVariete (_type_): _description_
        file_paramITK (_type_): _description_
        file_paramTypeSol (_type_): _description_

    Returns:
        _type_: _description_
    """
    paramVariete = load_paramVariete(file_paramVariete)
    paramITK = load_paramITK(file_paramITK)
    paramTypeSol = load_paramTypeSol(file_paramTypeSol)
    
    if ~np.isnan(paramITK["NI"]):
        print("NI NON NULL") 
        paramVariete["txConversion"] = paramVariete["NIYo"] + paramVariete["NIp"] * (1-np.exp(-paramVariete["NIp"] * paramITK["NI"])) - (np.exp(-0.5*((paramITK["NI"] - paramVariete["LGauss"])/paramVariete["AGauss"])* (paramITK["NI"]- paramVariete["LGauss"])/paramVariete["AGauss"]))/(paramVariete["AGauss"]*2.506628274631)

    return paramVariete, paramITK, paramTypeSol





def initialize_default_irrigation(data):
    # default irrigation scheme 
    data["irrigation"] = data["rain"] * 0
    data["irrigation"].attrs = {"units":"mm", "long_name":"irrigation"}
    return data




def load_iSDA_soil_data(data, grid_width, grid_height): 

    """
    This function loads iSDA soil data and crop to the area of interest remark :
    it would be nice to try to modulate the percentage of runoff according to
    slope

    First, this function loads the iSDA soil data, crops it to the area of
    interest and resamples it to match the grid resolution. The iSDA soil class
    raster map obtained is passed to the xarray dataset as a new variable.

    For the sake of example, the file that is used here already has been
    downsampled at TAMSAT resolution. Its specs are available on the CIRAD
    Dataverse at the following adress :
    https://doi.org/10.1038/s41598-021-85639-y

    Second, a correspondance table matching the iSDA soil classes to the soil
    physical properties is loaded. Maps of soil physical properties are then
    created and added to the xarray dataset.

    Returns:
        _type_: _description_
    """
    # load soil depth data, using the same code as in the load_iSDA_soil_data_alternate function
    soil_depth_file_path = "../data/assets/gyga_af_erzd__m_1km.tif"
    dataarray = rioxarray.open_rasterio(soil_depth_file_path)
    dataarray = dataarray.astype('float32') # converting to float32 to allow for NaNs
    dataarray = dataarray.rio.reproject_match(data, nodata=np.nan) # reprojecting to match the base data
    dataarray = dataarray.squeeze("band").drop_vars(["band"]) # removing the band dimension and variable
    dataarray = dataarray * 10 # converting from cm to mm
    data["profRu"] = dataarray # we add the soil depth data to the base data
    data["profRu"].attrs = {"units": "mm", "long_name": "Soil root zone depth (mm) adapted from Africa SoilGrids RZD"}
    del dataarray # we delete the temporary dataarray


    # load raster data
    soil_type_file_path = "../data/assets/iSDA_at_TAMSAT_resolution_zeroclass_1E6.tif"
    dataarray = rioxarray.open_rasterio(soil_type_file_path)

    # # determine the boundaries of the data xarray before cropping
    xmin, ymin, xmax, ymax = data.rio.set_spatial_dims(x_dim="x", y_dim="y").rio.bounds()

    # # crop to the area of interest
    dataarray = dataarray.where((dataarray.y < ymax)
                                & (dataarray.y > ymin)
                                & (dataarray.x > xmin)
                                & (dataarray.x < xmax)
                            ).dropna(dim='y', how='all').dropna(dim='x', how='all')

    # resample to match the grid resolution
    dataarray = dataarray.rio.reproject_match(data, nodata=np.nan)
    dataarray = dataarray.squeeze("band").drop_vars(["band"])
    dataarray.attrs = {"units":"arbitrary", "long_name":"soil_type"}

    # add soil type identifier to the dataset
    data["soil_type"] = dataarray
    data["soil_type"] = data["soil_type"] / 1000000 # conversion from 1E6 to 1E0
    data["soil_type"] = data["soil_type"].astype("float32")

    # load correspondance table
    path_soil_type_correspondance = "../data/assets/TypeSol_Moy13_HWSD.csv"
    df_soil_type_correspondance = pd.read_csv(path_soil_type_correspondance, sep=";", skiprows=1)

    # correspondance between soil properties naming in the csv file and in the dataset
    soil_variables = {
        "epaisseurProf" : "EpaisseurProf",
        "epaisseurSurf" : "EpaisseurSurf",
        "stockIniProf" : "StockIniProf",
        "stockIniSurf" : "StockIniSurf",
        "runoff_threshold" : "SeuilRuiss",
        "runoff_rate" : "PourcRuiss",
        "ru" : "Ru",
    }

    # create maps of soil properties and add them to the dataset
    for soil_variable in soil_variables :
        dict_values = dict(zip(df_soil_type_correspondance["Id"], df_soil_type_correspondance[soil_variables[soil_variable]]))
        dict_values[0] = np.nan
        soil_types_converted = np.reshape([dict_values[x.astype(int)] for x in data["soil_type"].to_numpy().flatten()], (grid_width, grid_height))
        data[soil_variable] = (data["soil_type"].dims,soil_types_converted)
        data[soil_variable] = data[soil_variable].astype("float32")
        # TODO: add dataarray.attrs = {} to precise units and long_name

    # converting pourcRuiss to decimal %
    data["runoff_rate"] = data["runoff_rate"] / 100

    return data




def load_iSDA_soil_data_alternate(data, grid_width, grid_height): 

    """
    This function loads iSDA soil data and crop to the area of interest remark :
    it would be nice to try to modulate the percentage of runoff according to
    slope

    First, this function loads the iSDA soil data, crops it to the area of
    interest and resamples it to match the grid resolution. The iSDA soil class
    raster map obtained is passed to the xarray dataset as a new variable.

    For the sake of example, the file that is used here already has been
    downsampled at TAMSAT resolution. Its specs are available on the CIRAD
    Dataverse at the following adress :
    https://doi.org/10.1038/s41598-021-85639-y

    Second, a correspondance table matching the iSDA soil classes to the soil
    physical properties is loaded. Maps of soil physical properties are then
    created and added to the xarray dataset.

    Returns:
        _type_: _description_
    """
    # loading soil depth data
    # soil data is Africa SoilGrids - Root zone depth (cm) 
    # reference of the dataset is https://data.isric.org/geonetwork/srv/fre/catalog.search#/metadata/c77d1209-56e9-4cac-b76e-bbf6c7e3a617
    # reference publication : https://doi.org/10.1016/j.geoderma.2018.02.046
    soil_depth_file_path = "../data/assets/gyga_af_erzd__m_1km.tif"
    dataarray = rioxarray.open_rasterio(soil_depth_file_path)
    dataarray = dataarray.astype('float32') # converting to float32 to allow for NaNs
    dataarray = dataarray.rio.reproject_match(data, nodata=np.nan) # reprojecting to match the base data
    dataarray = dataarray.squeeze("band").drop_vars(["band"]) # removing the band dimension and variable
    dataarray = dataarray * 10 # converting from cm to mm
    data["profRu"] = dataarray # we add the soil depth data to the base data
    data["profRu"].attrs = {"units": "mm", "long_name": "Soil root zone depth (mm) adapted from Africa SoilGrids RZD"}
    del dataarray # we delete the temporary dataarray


    # defining the soil surface reservoir depth with default values
    data["epaisseurSurf"] = 200 * xr.ones_like(data["profRu"])
    data["epaisseurSurf"].attrs = {"units": "mm", "long_name": "Soil surface reservoir depth (mm)"}


    # defining the initial water stock in the deep surface reservoir
    data["stockIniProf"] = 0 * xr.ones_like(data["profRu"])
    data["stockIniProf"].attrs = {"units": "mm", "long_name": "Initial water stock in the deep surface reservoir (mm)"}


    # loading soil texture data
    # soil data is adapted from iSDA Africa - USDA Soil Texture Class
    # reference of the original dataset is https://zenodo.org/record/4094616
    # reference of the adapted dataset is https://doi.org/10.18167/DVN1/YSVTS2 
    soil_texture_class_file_path = "../data/assets/iSDA_at_TAMSAT_resolution_zeroclass_1E6.tif"
    dataarray = rioxarray.open_rasterio(soil_texture_class_file_path)
    dataarray = dataarray.rio.reproject_match(data, nodata=np.nan) # reprojecting to match the base data
    dataarray = dataarray.squeeze("band").drop_vars(["band"]) # removing the band dimension and variable
    dataarray.attrs = {"units":"arbitrary", "long_name":"soil_type"} # adding attributes

    data["soil_type"] = dataarray # add soil type identifier to the dataset
    data["soil_type"] = data["soil_type"] / 1000000 # conversion from 1E6 to 1E0
    data["soil_type"] = data["soil_type"].astype("float32")

    # load correspondance table
    path_soil_type_correspondance = "../data/assets/TypeSol_Moy13_HWSD.csv"
    df_soil_type_correspondance = pd.read_csv(path_soil_type_correspondance, sep=";", skiprows=1)

    # correspondance between soil properties naming in the csv file and in the dataset
    soil_variables = {
        "runoff_threshold" : "SeuilRuiss", # utilisé dans bilan_hydro.estimate_runoff pour le calcul de lr
        "runoff_rate" : "PourcRuiss", # utilisé dans bilan_hydro.estimate_runoff pour le calcul de lr
    }

    # create maps of soil properties and add them to the dataset
    for soil_variable in soil_variables :
        dict_values = dict(zip(df_soil_type_correspondance["Id"], df_soil_type_correspondance[soil_variables[soil_variable]]))
        dict_values[0] = np.nan
        soil_types_converted = np.reshape([dict_values[x.astype(int)] for x in data["soil_type"].to_numpy().flatten()], (grid_width, grid_height))
        data[soil_variable] = (data["soil_type"].dims,soil_types_converted)
        data[soil_variable] = data[soil_variable].astype("float32")
        # TODO: add dataarray.attrs = {} to precise units and long_name

    # converting pourcRuiss to decimal %
    data["runoff_rate"] = data["runoff_rate"] / 100
    del dataarray # we delete the temporary dataarray


    # loading RU
    soil_RZPAWC_file_path = "../data/assets/gyga_af_agg_erzd_tawcpf23mm__m_1km.tif"
    dataarray = rioxarray.open_rasterio(soil_RZPAWC_file_path)
    dataarray = dataarray.astype('float32')
    dataarray = dataarray.rio.reproject_match(data, nodata=np.nan) # reprojecting to match the base data
    dataarray = dataarray.squeeze("band").drop_vars(["band"]) # removing the band dimension and variable
    dataarray.attrs = {"units":"mm", "long_name":"Root zone plant available water capacity (mm)"} # adding attributes
    data["RZPAWC"] = dataarray # add soil type identifier to the dataset
    del dataarray # we delete the temporary dataarray

    #calculating RU (mm/m)
    data["ru"] = data["RZPAWC"] / (data["profRu"]/1000)

    return data





def calc_day_length(day, lat):
    """
    This function calculates the day length for a given day and latitude.

    Args:
        day (_type_): _description_
        lat (_type_): _description_

    Returns:
        _type_: _description_
    """
    # print(day, lat)
    coords = LocationInfo(latitude=float(lat), longitude=0.0)
    daylight = astral.sun.daylight(coords.observer, date=day)
    dureeDuJour = (daylight[1] - daylight[0]).seconds/3600
    return dureeDuJour





def calc_day_length_raster_fast(data, date_start, duration):

    vectorized_func = np.vectorize(calc_day_length)

    days = np.array([date_start + datetime.timedelta(days=i) for i in range(duration)])[...,np.newaxis]
    latitudes = np.array(data["y"])[np.newaxis,...]

    result = vectorized_func(days, latitudes)

    # we will first define an empty array of the same shape as the rain array
    data["dureeDuJour"] = (data["rain"].dims, np.zeros(data["rain"].shape))
    data["dureeDuJour"].values = np.repeat(result[...,np.newaxis], data["dureeDuJour"].shape[2], axis=2)

    return data





