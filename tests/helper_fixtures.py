"""Input grids and a reference calculation for day-length tests."""
import datetime as dt
import numpy as np
import xarray as xr
from sarra_py import calc_day_length


def reference_calc_day_length_raster_fast(data, date_start, duration):
    """Previous uncached implementation, kept as a numerical regression reference."""
    vectorized_func = np.vectorize(calc_day_length)

    days = np.array([date_start + dt.timedelta(days=i) for i in range(duration)])[..., np.newaxis]
    latitudes = np.array(data["y"])[np.newaxis, ...]
    result = vectorized_func(days, latitudes)

    data["dureeDuJour"] = (data["rain"].dims, np.zeros(data["rain"].shape))
    data["dureeDuJour"].values = np.repeat(result[..., np.newaxis], data["dureeDuJour"].shape[2], axis=2)
    return data


def build_recent_notebook_input(duration=45, width=8, height=7, seed=4321):
    rng = np.random.default_rng(seed)
    date_start = dt.date(2023, 4, 1)
    time_coord = np.array([date_start + dt.timedelta(days=i) for i in range(duration)], dtype=object)
    y = np.linspace(6.8, 13.19, height, dtype="float64")
    x = np.linspace(11.43, 16.36, width, dtype="float64")
    dims = ("time", "y", "x")
    soil_dims = ("y", "x")

    rain = rng.gamma(shape=1.2, scale=4.0, size=(duration, height, width)).astype("float32")
    rain[30:40, :, :] += 12.0
    tmax = (33.0 + rng.normal(0.0, 1.5, size=(duration, height, width))).astype("float32")
    tmin = (22.0 + rng.normal(0.0, 1.0, size=(duration, height, width))).astype("float32")
    tp_moy = (tmax + tmin) / 2
    rg = (18.0 + rng.normal(0.0, 1.0, size=(duration, height, width))).astype("float32")
    et0 = 0.0023 * np.sqrt(np.maximum(tmax - tmin, 0.0)) * (tp_moy + 17.8) * rg

    soil_shape = (height, width)
    data = xr.Dataset(
        data_vars={
            "rain": (dims, rain, {"units": "mm", "long_name": "rainfall"}),
            "tpMoy": (dims, tp_moy, {"units": "degC", "long_name": "mean temperature"}),
            "rg": (dims, rg, {"units": "MJ/m2", "long_name": "solar radiation"}),
            "ET0": (dims, et0.astype("float32"), {"units": "mm d-1", "long_name": "ET0 Hargreaves"}),
            "ru": (soil_dims, np.full(soil_shape, 150.0, dtype="float32")),
            "epaisseurSurf": (soil_dims, np.full(soil_shape, 200.0, dtype="float32")),
            "epaisseurProf": (soil_dims, np.full(soil_shape, 1400.0, dtype="float32")),
            "profRu": (soil_dims, np.full(soil_shape, 1600.0, dtype="float32")),
            "stockIniProf": (soil_dims, np.full(soil_shape, 30.0, dtype="float32")),
            "stockIniSurf": (soil_dims, np.full(soil_shape, 0.0, dtype="float32")),
            "runoff_threshold": (soil_dims, np.full(soil_shape, 25.0, dtype="float32")),
            "runoff_rate": (soil_dims, np.full(soil_shape, 0.08, dtype="float32")),
        },
        coords={"time": time_coord, "y": y, "x": x},
        attrs={"source": "synthetic notebook regression inputs"},
    )
    return data, date_start
