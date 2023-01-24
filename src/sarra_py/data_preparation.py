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


def get_grid_size(TAMSAT_path, date_start, duration):

    TAMSAT_files = [f for f in listdir(TAMSAT_path) if isfile(join(TAMSAT_path, f))]
    TAMSAT_files_df = pd.DataFrame({"filename":TAMSAT_files})

    TAMSAT_files_df["date"] = TAMSAT_files_df.apply(
        lambda x: datetime.date(
            int(x["filename"].replace(".tif","").split("_")[-3]),
            int(x["filename"].replace(".tif","").split("_")[-2]),
            int(x["filename"].replace(".tif","").split("_")[-1]),
        ),
        axis=1,
    )

    TAMSAT_files_df = TAMSAT_files_df[(TAMSAT_files_df["date"]>=date_start) & (TAMSAT_files_df["date"]<date_start+datetime.timedelta(days=duration))].reset_index(drop=True)


    src = rasterio.open(os.path.join(TAMSAT_path,TAMSAT_files_df.loc[0,"filename"]))
    array = src.read(1)
    grid_width = array.shape[0]
    grid_height = array.shape[1]

    return grid_width, grid_height




def load_TAMSAT_data(data, TAMSAT_path, date_start, duration):
    # Building index of TAMSAT rainfall geotiffs

    data = data.copy(deep=True)

    TAMSAT_files = [f for f in listdir(TAMSAT_path) if isfile(join(TAMSAT_path, f))]
    TAMSAT_files_df = pd.DataFrame({"filename":TAMSAT_files})

    TAMSAT_files_df["date"] = TAMSAT_files_df.apply(
        lambda x: datetime.date(
            int(x["filename"].replace(".tif","").split("_")[-3]),
            int(x["filename"].replace(".tif","").split("_")[-2]),
            int(x["filename"].replace(".tif","").split("_")[-1]),
        ),
        axis=1,
    )

    TAMSAT_files_df = TAMSAT_files_df[(TAMSAT_files_df["date"]>=date_start) & (TAMSAT_files_df["date"]<date_start+datetime.timedelta(days=duration))].reset_index(drop=True)

    # reading the first file as rainfall grid size defines output resolution

    # src = rasterio.open(os.path.join(TAMSAT_path,TAMSAT_files_df.loc[0,"filename"]))
    # array = src.read(1)
    # grid_width = array.shape[0]
    # grid_height = array.shape[1]


    # checking if dataarray_full already exists
    try:
        del dataarray_full
    except:
        pass

    for i in range(duration):
        # loading raster
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




def load_AgERA5_data(data, AgERA5_data_path, date_start, duration): # listing available variables from the list of subfolders

    data = data.copy(deep=True)

    AgERA5_variables = [path.split("/")[-1] for path in [x[0] for x in os.walk(AgERA5_data_path)][1:]]

    # defining dict of dfs, one df per variable
    AgERA5_files_df_collection = {}
    for variable in AgERA5_variables:
        AgERA5_files = [f for f in listdir(os.path.join(AgERA5_data_path,variable)) if isfile(join(os.path.join(AgERA5_data_path,variable), f))]
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


    AgERA5_SARRA_correspondance = {
        '10m_wind_speed_24_hour_mean':None,
        '2m_temperature_24_hour_maximum':None,
        '2m_temperature_24_hour_mean':'tpMoy',
        '2m_temperature_24_hour_minimum':None,
        'ET0Hargeaves':'ET0',
        'solar_radiation_flux_daily':'rg',
        'vapour_pressure_24_hour_mean':None,
    }

    for variable in tqdm(AgERA5_variables) :
        if AgERA5_SARRA_correspondance[variable] != None :

            try:
                del dataarray_full
            except:
                pass

            # data[AgERA5_SARRA_correspondance[variable]] = np.empty((grid_width, grid_height, duration))

            for i in range(duration) :
                dataarray = rioxarray.open_rasterio(os.path.join(AgERA5_data_path,variable,AgERA5_files_df_collection[variable].loc[i,"filename"]))
                dataarray = dataarray.rio.reproject_match(data, nodata=np.nan)
                dataarray = dataarray.squeeze("band").drop_vars(["band"])
                # TODO: add dataarray.attrs = {} to precise units and long_name

                try:
                    dataarray_full = xr.concat([dataarray_full, dataarray],"time")
                except:
                    dataarray_full = dataarray

            data[AgERA5_SARRA_correspondance[variable]] = dataarray_full
            

    data["rg"] = data["rg"]/1000
    
    return data




def load_paramVariete(file_paramVariete) :

    with open(os.path.join('../data/params/variety/',file_paramVariete), 'r') as stream:
        paramVariete = yaml.safe_load(stream)
    if paramVariete["feuilAeroBase"] == 0.1 :
        raise exception()
    return paramVariete


def load_paramITK(file_paramITK):

    with open(os.path.join('../data/params/itk/',file_paramITK), 'r') as stream:
        paramITK = yaml.safe_load(stream)
    paramITK["DateSemis"] = datetime.datetime.strptime(paramITK["DateSemis"], "%Y-%m-%d").date()
    return paramITK


def load_paramTypeSol(file_paramTypeSol):
    with open(os.path.join('../data/params/soil/',file_paramTypeSol), 'r') as stream:
        paramTypeSol = yaml.safe_load(stream)     
    return paramTypeSol

def load_YAML_parameters(file_paramVariete, file_paramITK, file_paramTypeSol):
    paramVariete = load_paramVariete(file_paramVariete)
    paramITK = load_paramITK(file_paramITK)
    paramTypeSol = load_paramTypeSol(file_paramTypeSol)
    
    if ~np.isnan(paramITK["NI"]):
        print("NI NON NULL") 
        paramVariete["txConversion"] = paramVariete["NIYo"] + paramVariete["NIp"] * (1-np.exp(-paramVariete["NIp"] * paramITK["NI"])) - (np.exp(-0.5*((paramITK["NI"] - paramVariete["LGauss"])/paramVariete["AGauss"])* (paramITK["NI"]- paramVariete["LGauss"])/paramVariete["AGauss"]))/(paramVariete["AGauss"]*2.506628274631)

    return paramVariete, paramITK, paramTypeSol





"""
# Alternatively, building index of CHIRPS rainfall geotiffs

CHIRPS_files = [f for f in listdir(CHIRPS_path) if isfile(join(CHIRPS_path, f))]
CHIRPS_files_df = pd.DataFrame({"filename":CHIRPS_files})

CHIRPS_files_df["date"] = CHIRPS_files_df.apply(
    lambda x: datetime.date(
        int(x["filename"].replace(".tif","").split("_")[-3]),
        int(x["filename"].replace(".tif","").split("_")[-2]),
        int(x["filename"].replace(".tif","").split("_")[-1]),
    ),
    axis=1,
)

CHIRPS_files_df = CHIRPS_files_df[(CHIRPS_files_df["date"]>=date_start) & (CHIRPS_files_df["date"]<date_start+datetime.timedelta(days=duration))].reset_index(drop=True)



import numpy as np

data = {}

# rain
data["rain"] = np.empty((grid_width, grid_height, duration))
for i in range(duration):
    dataset = rasterio.open(os.path.join(TAMSAT_path,TAMSAT_files_df.loc[i,"filename"]))
    data["rain"][:,:,i] = dataset.read(1)
    dataset.close()




from rasterio.enums import Resampling


# resampling methods can be 'nearest', 'bilinear', 'cubic', 'cubic_spline', 'lanczos', 'average', 'mode', 'gauss'
# we'll stick to nearest 
resampling_method = "nearest"


data["rain_CHIRPS"] = np.empty((grid_width, grid_height, duration))

for i in tqdm(range(duration), leave=False) :
    dataset = rasterio.open(os.path.join(CHIRPS_path,CHIRPS_files_df.loc[i,"filename"]))
    arr = dataset.read(
            out_shape=(
                dataset.count,
                grid_width,
                grid_height,
            ),
            resampling=getattr(Resampling, resampling_method)
        )[0]
    data["rain_CHIRPS"][:,:,i] = arr
    dataset.close()
"""




"""
from rasterio.enums import Resampling

AgERA5_SARRA_correspondance = {
    '10m_wind_speed_24_hour_mean':None,
    '2m_temperature_24_hour_maximum':None,
    '2m_temperature_24_hour_mean':'tpMoy',
    '2m_temperature_24_hour_minimum':None,
    'ET0Hargeaves':'ET0',
    'solar_radiation_flux_daily':'rg',
    'vapour_pressure_24_hour_mean':None,
}


# resampling methods can be 'nearest', 'bilinear', 'cubic', 'cubic_spline', 'lanczos', 'average', 'mode', 'gauss'
# we'll stick to nearest 
resampling_method = "nearest"


for variable in tqdm(AgERA5_variables) :
    if AgERA5_SARRA_correspondance[variable] != None :

        data[AgERA5_SARRA_correspondance[variable]] = np.empty((grid_width, grid_height, duration))

        for i in tqdm(range(duration), leave=False, desc="variable {variable}") :
            dataset = rasterio.open(os.path.join(AgERA5_data_path,variable,AgERA5_files_df_collection[variable].loc[i,"filename"]))

            arr = dataset.read(
                    out_shape=(
                        dataset.count,
                        grid_width,
                        grid_height,
                    ),
                    resampling=getattr(Resampling, resampling_method)
                )[0]

            data[AgERA5_SARRA_correspondance[variable]][:,:,i] = arr
            dataset.close()

# correcting rg
data["rg"] = data["rg"]/1000

# default irrigation scheme 
data["irrigation"] = np.empty((grid_width, grid_height, duration))
"""


def initialize_default_irrigation(data):
    # default irrigation scheme 
    data["irrigation"] = data["rain"] * 0
    data["irrigation"].attrs = {"units":"mm", "long_name":"irrigation"}
    return data




def load_iSDA_soil_data(data, grid_width, grid_height): 

    """ 
    Load iSDA soil data and crop to the area of interest

    """

    data = data.copy(deep=True)

    soil_type_file_path = "/mnt/d/Mes Donnees/SARRA_data-download/soil_maps/iSDA_at_TAMSAT_resolution_zeroclass_1E6.tif"
    dataarray = rioxarray.open_rasterio(soil_type_file_path)

    area = {
        'burkina': [16, -6, 9, 3], #lat,lon lat,lon
        }
    selected_area = "burkina"

    dataarray = dataarray.where((dataarray.y < area[selected_area][0])
                                & (dataarray.y > area[selected_area][2])
                                & (dataarray.x > area[selected_area][1])
                                & (dataarray.x < area[selected_area][3])
                            ).dropna(dim='y', how='all').dropna(dim='x', how='all')

    dataarray = dataarray.rio.reproject_match(data, nodata=np.nan)
    dataarray = dataarray.squeeze("band").drop_vars(["band"])
    dataarray.attrs = {"units":"arbitrary", "long_name":"soil_type"}


    data["soil_type"] = dataarray
    data["soil_type"] = data["soil_type"] / 1000000


    # load correspondance table
    path_soil_type_correspondance = "/mnt/g/Mon Drive/CIRAD/SARRA-O/Sarraojarexe/Sarraojarexe/data/csvTypeSol/TypeSol_Moy13_HWSD.csv"
    df_soil_type_correspondance = pd.read_csv(path_soil_type_correspondance, sep=";", skiprows=1)


    # epaisseurProf: 1300.0
    # epaisseurSurf: 200.0
    # stockIniProf: 170.0
    # stockIniSurf: 30.0

    # # params type sol
    # seuilRuiss: 20.0
    # pourcRuiss: 0.3
    # ru: 132.0

    # # non utilisés mais présents dans sarra-h
    # HumCR: 0.32
    # HumFC: 0.32
    # HumPF: 0.18
    # HumSat: 0.48
    # Pevap: 0.2
    # PercolationMax: 5.0


    
    # nom dans SARRA-Py : nom dans le df
    soil_variables = {
        "epaisseurProf" : "EpaisseurProf",
        "epaisseurSurf" : "EpaisseurSurf",
        "stockIniProf" : "StockIniProf",
        "stockIniSurf" : "StockIniSurf",
        "seuilRuiss" : "SeuilRuiss",
        "pourcRuiss" : "PourcRuiss",
        "ru" : "Ru",
    }

    for soil_variable in soil_variables :
        dict_values = dict(zip(df_soil_type_correspondance["Id"], df_soil_type_correspondance[soil_variables[soil_variable]]))
        dict_values[0] = np.nan
        soil_types_converted = np.reshape([dict_values[x.astype(int)] for x in data["soil_type"].to_numpy().flatten()], (grid_width, grid_height))
        data[soil_variable] = (data["soil_type"].dims,soil_types_converted)
        # TODO: add dataarray.attrs = {} to precise units and long_name

    return data
