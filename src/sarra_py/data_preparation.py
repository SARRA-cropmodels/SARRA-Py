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
from functools import lru_cache





def build_rainfall_files_df(rainfall_path, date_start, duration):
    """List daily TIFF rasters in date order and require complete coverage."""
    if duration <= 0:
        raise ValueError("duration must be positive")

    date_end = date_start + datetime.timedelta(days=duration)
    rows = []
    with os.scandir(rainfall_path) as entries:
        for entry in entries:
            if not entry.is_file() or not entry.name.lower().endswith(".tif"):
                continue
            parts = os.path.splitext(entry.name)[0].rsplit("_", 3)
            if len(parts) != 4:
                raise ValueError(f"Cannot read date from raster filename: {entry.name}")
            try:
                file_date = datetime.date(*(int(part) for part in parts[1:]))
            except ValueError as exc:
                raise ValueError(f"Cannot read date from raster filename: {entry.name}") from exc
            if date_start <= file_date < date_end:
                rows.append((entry.name, file_date))

    files = pd.DataFrame(rows, columns=["filename", "date"])
    files = files.sort_values(["date", "filename"]).reset_index(drop=True)
    expected_dates = [date_start + datetime.timedelta(days=i) for i in range(duration)]
    if files["date"].tolist() != expected_dates:
        missing_dates = sorted(set(expected_dates) - set(files["date"]))
        duplicate_dates = files.loc[files["date"].duplicated(), "date"].tolist()
        raise ValueError(
            f"Incomplete daily rasters in {rainfall_path}: "
            f"missing dates {missing_dates}, duplicate dates {duplicate_dates}"
        )
    return files


def _ensure_daily_time(data, date_start, duration):
    """Align positional time indices or reject conflicting calendar dates."""
    if "time" not in data.sizes:
        return
    if data.sizes["time"] != duration:
        raise ValueError("Existing time dimension does not match duration")
    expected = np.datetime64(date_start.isoformat(), "D") + np.arange(duration)
    values = np.asarray(data["time"].values)
    if np.issubdtype(values.dtype, np.datetime64):
        if not np.array_equal(values.astype("datetime64[D]"), expected):
            raise ValueError("Existing time coordinates do not match requested dates")
    elif values.dtype.kind in "iu" and np.array_equal(values, np.arange(duration)):
        data.coords["time"] = expected.astype("datetime64[ns]")
    else:
        raise ValueError("Existing time coordinates must be dates or consecutive indices from zero")


def get_grid_size(rainfall_path, date_start, duration):
    """Return (y rows, x columns) of the first requested rainfall raster.

    Require one date-coded TIFF for each day in the requested period."""

    rainfall_files_df = build_rainfall_files_df(rainfall_path, date_start, duration)

    # loading the first rainfall file to get the grid size
    with rasterio.open(os.path.join(rainfall_path, rainfall_files_df.loc[0, "filename"])) as src:
        array = src.read(1)
    grid_width = array.shape[0]
    grid_height = array.shape[1]

    return grid_width, grid_height




def load_TAMSAT_data(data, TAMSAT_path, date_start, duration):
    """Add daily rainfall in mm to data and return the same Dataset.

    Require one date-coded TIFF per day on a consistent grid."""

    TAMSAT_files_df = build_rainfall_files_df(TAMSAT_path, date_start, duration)
    _ensure_daily_time(data, date_start, duration)
    arrays = []
    for filename in TAMSAT_files_df["filename"]:
        raster = rioxarray.open_rasterio(os.path.join(TAMSAT_path, filename))
        try:
            daily = raster.squeeze("band").drop_vars(["band", "spatial_ref"])
            daily.attrs = {}
            arrays.append(daily.load())
        finally:
            raster.close()

    dates = np.asarray(TAMSAT_files_df["date"], dtype="datetime64[ns]")
    dataarray_full = xr.concat(arrays, dim=xr.IndexVariable("time", dates), join="exact")
    dataarray_full.rio.write_crs(4326, inplace=True)
    data["rain"] = dataarray_full
    data["rain"].attrs = {"units":"mm", "long_name":"rainfall"}

    return data




def load_TAMSAT_data_fast(data, rainfall_data_path, date_start, duration):
    """Load daily TAMSAT rainfall rasters with ``xarray.open_mfdataset``.

    Uses the same local date-coded convention as `load_TAMSAT_data`, removes
    the raster band dimension, and stores `band_data` as daily rainfall.

    Source status: code-observed local loader.
    """

    rainfall_data_path_df = build_rainfall_files_df(rainfall_data_path, date_start, duration)
    _ensure_daily_time(data, date_start, duration)
    dataarray_full = xr.open_mfdataset([os.path.join(rainfall_data_path,rainfall_data_path_df.loc[i,"filename"]) for i in range(len(rainfall_data_path_df))], concat_dim="time", combine="nested", chunks={"x":100,"y":100})
    dataarray_full = dataarray_full.squeeze("band").drop_vars(["band"])
    dataarray_full = dataarray_full.assign_coords(
        time=np.asarray(rainfall_data_path_df["date"], dtype="datetime64[ns]")
    )
    dataarray_full.rio.write_crs(4326,inplace=True)
    data["rain"] = dataarray_full["band_data"]

    return data





def _list_agera5_files(data_path, date_start, duration):
    """Select complete daily raster series for each AgERA5 folder."""
    variables = sorted(entry.name for entry in os.scandir(data_path) if entry.is_dir())
    forcing_variables = {
        "2m_temperature_24_hour_mean", "ET0Hargeaves", "solar_radiation_flux_daily"
    }
    files = {
        variable: build_rainfall_files_df(os.path.join(data_path, variable), date_start, duration)
        for variable in variables if variable in forcing_variables
    }
    return variables, files


def load_AgERA5_data(data, AgERA5_data_path, date_start, duration, progress=True):
    """Add temperature, ET0 and radiation to a rainfall grid.

    Read complete daily TIFF series, reproject to data and divide local
    radiation values by 1000 before storing rg."""
    AgERA5_variables, AgERA5_files_df_collection = _list_agera5_files(
        AgERA5_data_path, date_start, duration
    )
    _ensure_daily_time(data, date_start, duration)
    required = {"2m_temperature_24_hour_mean", "ET0Hargeaves", "solar_radiation_flux_daily"}
    missing = sorted(required - AgERA5_files_df_collection.keys())
    if missing:
        raise ValueError(f"Missing AgERA5 forcing folders: {', '.join(missing)}")

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
    for variable in tqdm(AgERA5_variables, disable=not progress):
        if progress:
            print(variable)
        if AgERA5_SARRA_correspondance.get(variable) is not None:

            files = AgERA5_files_df_collection[variable]
            arrays = []
            for filename in files["filename"]:
                raster = rioxarray.open_rasterio(os.path.join(AgERA5_data_path, variable, filename))
                try:
                    daily = raster.rio.reproject_match(data, nodata=np.nan)
                    arrays.append(daily.squeeze("band").drop_vars(["band"]).load())
                finally:
                    raster.close()

            dates = np.asarray(files["date"], dtype="datetime64[ns]")
            dataarray_full = xr.concat(arrays, dim=xr.IndexVariable("time", dates), join="exact")

            # storing the variable in the data dictionary
            data[AgERA5_SARRA_correspondance[variable]] = dataarray_full
            
    # unit conversion for solar radiation (kJ/m2 as provided by AgERA5 to MJ/m2/day)
    data["rg"] = data["rg"]/1000
    
    return data





def load_AgERA5_data_fast_dask(data, AgERA5_data_path, date_start, duration):
    """Load AgERA5 forcing rasters used by SARRA-Py notebooks.

    Fast variant using `open_mfdataset`; maps local folders to `tpMoy`, `ET0`
    and `rg`, reprojects to the base grid, and divides `rg` by 1000.

    Source status: code-observed local conversion; AgERA5 source units should
    be verified against preprocessing.
    """
    AgERA5_variables, AgERA5_files_df_collection = _list_agera5_files(
        AgERA5_data_path, date_start, duration
    )
    _ensure_daily_time(data, date_start, duration)
    required = {"2m_temperature_24_hour_mean", "ET0Hargeaves", "solar_radiation_flux_daily"}
    missing = sorted(required - AgERA5_files_df_collection.keys())
    if missing:
        raise ValueError(f"Missing AgERA5 forcing folders: {', '.join(missing)}")

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
        if AgERA5_SARRA_correspondance.get(variable) is not None:

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
            dataarray_full = dataarray_full.assign_coords(
                time=np.asarray(AgERA5_files_df_collection[variable]["date"], dtype="datetime64[ns]")
            )
            dataarray_full = dataarray_full.rio.reproject_match(data, nodata=np.nan)

            
            dataarray_full.rio.write_crs(4326,inplace=True)
            
            
            data[AgERA5_SARRA_correspondance[variable]] = dataarray_full["band_data"]

            
    # unit conversion for solar radiation (kJ/m2 as provided by AgERA5 to MJ/m2/day)
    data["rg"] = data["rg"]/1000
    
    return data









def load_paramVariete(file_paramVariete) :
    """Load variety parameters from ../data/params/variety relative to cwd."""
    with open(os.path.join('../data/params/variety/',file_paramVariete), 'r') as stream:
        paramVariete = yaml.safe_load(stream)
    if paramVariete["feuilAeroBase"] == 0.1 :
        raise Exception()
    return paramVariete





def load_paramITK(file_paramITK):
    """Load management parameters from ../data/params/itk and parse DateSemis."""
    with open(os.path.join('../data/params/itk/',file_paramITK), 'r') as stream:
        paramITK = yaml.safe_load(stream)
    paramITK["DateSemis"] = datetime.datetime.strptime(paramITK["DateSemis"], "%Y-%m-%d").date()
    return paramITK





def load_paramTypeSol(file_paramTypeSol):
    """Load soil parameters from ../data/params/soil relative to cwd."""
    with open(os.path.join('../data/params/soil/',file_paramTypeSol), 'r') as stream:
        paramTypeSol = yaml.safe_load(stream)     
    return paramTypeSol





def load_YAML_parameters(file_paramVariete, file_paramITK, file_paramTypeSol):
    """Return (variety, management, soil) mappings from legacy YAML loaders.

    Accept absolute paths or filenames under ../data/params; preserve the
    existing variety adjustment based on management NI."""
    paramVariete = load_paramVariete(file_paramVariete)
    paramITK = load_paramITK(file_paramITK)
    paramTypeSol = load_paramTypeSol(file_paramTypeSol)
    
    if ~np.isnan(paramITK["NI"]):
        print("NI NON NULL") 
        paramVariete["txConversion"] = paramVariete["NIYo"] + paramVariete["NIp"] * (1-np.exp(-paramVariete["NIp"] * paramITK["NI"])) - (np.exp(-0.5*((paramITK["NI"] - paramVariete["LGauss"])/paramVariete["AGauss"])* (paramITK["NI"]- paramVariete["LGauss"])/paramVariete["AGauss"]))/(paramVariete["AGauss"]*2.506628274631)

    return paramVariete, paramITK, paramTypeSol





def initialize_default_irrigation(data):
    """Add a zero daily irrigation variable with the same grid as `rain`."""
    # default irrigation scheme 
    data["irrigation"] = data["rain"] * 0
    data["irrigation"].attrs = {"units":"mm", "long_name":"irrigation"}
    return data




def load_iSDA_soil_data(data, grid_width, grid_height): 

    """Add soil depth and class-based properties to data on its grid.

    Read local data/assets rasters and the soil class table; return data."""
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

    """Add soil depth, class properties and raster-derived ru to data.

    Read local data/assets files and return data on the input grid."""
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
        "epaisseurProf": "EpaisseurProf",
        "stockIniSurf": "StockIniSurf",
        "runoff_threshold": "SeuilRuiss",
        "runoff_rate": "PourcRuiss",
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
    """Compute daylight duration for one date and latitude.

    Uses Astral sunrise/sunset daylight and fixes longitude to 0.0; the result
    is returned in hours.

    Source status: source-related to Astral daylight calculation; longitude
    convention is a SARRA-Py implementation choice.
    """
    # print(day, lat)
    coords = LocationInfo(latitude=float(lat), longitude=0.0)
    daylight = astral.sun.daylight(coords.observer, date=day)
    dureeDuJour = (daylight[1] - daylight[0]).seconds/3600
    return dureeDuJour



def _normalize_day_length_date(date_start):
    """Normalize a day-length start date for the LRU cache key."""
    if isinstance(date_start, datetime.datetime):
        return date_start.date().isoformat()
    if isinstance(date_start, datetime.date):
        return date_start.isoformat()
    if hasattr(date_start, "item"):
        return _normalize_day_length_date(date_start.item())
    return str(date_start)


@lru_cache(maxsize=64)
def _cached_day_length_matrix(date_start_key, duration, latitudes):
    """Compute or reuse daylight hours for each day and latitude."""
    date_start = datetime.date.fromisoformat(date_start_key)
    vectorized_func = np.vectorize(calc_day_length)

    days = np.array(
        [date_start + datetime.timedelta(days=i) for i in range(duration)],
        dtype=object,
    )[..., np.newaxis]
    latitudes_array = np.asarray(latitudes, dtype=float)[np.newaxis, ...]

    return np.asarray(vectorized_func(days, latitudes_array), dtype=float)


def _broadcast_day_length_to_rain(day_length_by_latitude, rain):
    """Broadcast a `(time, y)` day-length matrix to the rainfall grid."""
    if "time" not in rain.dims or "y" not in rain.dims:
        raise ValueError("rain must have 'time' and 'y' dimensions to compute day length")

    shape = [1] * rain.ndim
    shape[rain.dims.index("time")] = rain.shape[rain.dims.index("time")]
    shape[rain.dims.index("y")] = rain.shape[rain.dims.index("y")]

    values = day_length_by_latitude.reshape(shape)
    return np.broadcast_to(values, rain.shape).copy()




def calc_day_length_raster_fast(data, date_start, duration):
    """Add a cached day-length raster to a simulation dataset.

    Computes daylight from date and `y` latitude, then broadcasts it to the
    shape of `rain`. The dataset is mutated in place.

    Source status: code-observed grid broadcast around Astral day length.
    """

    latitudes = tuple(float(value) for value in np.asarray(data["y"].values))
    date_start_key = _normalize_day_length_date(date_start)
    result = _cached_day_length_matrix(date_start_key, int(duration), latitudes)
    values = _broadcast_day_length_to_rain(result, data["rain"])
    data["dureeDuJour"] = (data["rain"].dims, values)

    return data
