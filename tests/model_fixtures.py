"""Small deterministic inputs and comparisons for model regression tests."""
import datetime as dt
import numpy as np
import xarray as xr
from sarra_py import calculate_once_daily_thermal_time, initialize_default_irrigation, initialize_simulation


def sample_variety_params():
    return {
        "SDJLevee": 70.0,
        "SDJBVP": 700.0,
        "SDJRPR": 400.0,
        "SDJMatu1": 300.0,
        "SDJMatu2": 150.0,
        "KRdtPotA": 0.5,
        "KRdtPotB": 100.0,
        "PPExp": 0.12,
        "SeuilPP": 13.6,
        "PPsens": 0.66,
        "PPCrit": 11.0,
        "TBase": 11.0,
        "TOpt1": 32.0,
        "TOpt2": 36.0,
        "TLim": 46.0,
        "pcReallocFeuille": 0.6,
        "txConversion": 5.0,
        "txAssimBVP": 1.0,
        "txAssimMatu1": 0.9,
        "txAssimMatu2": 0.7,
        "kRespMaint": 0.01,
        "aeroTotBase": 0.6,
        "aeroTotPente": 5.0e-05,
        "feuilAeroBase": 0.65,
        "feuilAeroPente": -0.0002,
        "txRealloc": 0.4,
        "tempMaint": 25.0,
        "kcMax": 1.15,
        "PFactor": 0.55,
        "seuilCstrMortality": 3.0,
        "kdf": 0.4,
        "txResGrain": 0.5,
        "VRacLevee": 35.0,
        "VRacBVP": 35.0,
        "VRacPSP": 35.0,
        "VRacRPR": 35.0,
        "VRacMatu1": 25.0,
        "VRacMatu2": 25.0,
        "slaMin": 0.0016,
        "slaMax": 0.008,
        "slaPente": 0.4,
        "densiteA": 0.7,
        "densiteP": 4.5,
        "densOpti": 53333.0,
        "AGauss": 1.0,
        "KRdtBiom": 0.0,
        "LGauss": 1.0,
        "NIYo": 1.0,
        "NIp": 0.0,
        "phaseDevVeg": 0,
        "poidsSecGrain": 0.028,
        "senCO2": 10.0,
    }


def sample_itk_params(date_start):
    return {
        "DateSemis": date_start,
        "NI": np.nan,
        "coefMc": 0.0,
        "densite": 53333.0,
        "nbjTestSemis": 0,
        "profRacIni": 120.0,
        "seuilEauSemis": 8.0,
        "irrigAuto": False,
        "irrigAutoTarget": 0.0,
        "maxIrrig": 0.0,
        "surfMc": 1.0,
        "biomIniMc": 0.0,
        "humSatMc": 0.0,
        "mulch": 1.0,
        "KI": 0.0,
        "KNLit": 0.0,
        "KNUp": 0.0,
        "KT": 0.0,
        "DisMc": 0,
        "TxRecolte": 0.0,
        "TxaTerre": 0.0,
        "NbUBT": 10.0,
        "dateFin": 300.0,
        "precision": 0.0,
    }


def sample_soil_params():
    return {}


def build_input_dataset(duration=45, width=8, height=7, seed=1234):
    rng = np.random.default_rng(seed)
    dims = ("time", "x", "y")
    coords = {
        "time": np.arange(duration),
        "x": np.arange(width),
        "y": np.arange(height),
    }

    rain = rng.gamma(shape=1.2, scale=4.0, size=(duration, width, height)).astype("float32")
    rain[0:5, :, :] += 10.0
    tp_moy = (28.0 + rng.normal(0.0, 1.5, size=(duration, width, height))).astype("float32")
    rg = (18.0 + rng.normal(0.0, 1.0, size=(duration, width, height))).astype("float32")
    et0 = (4.5 + rng.normal(0.0, 0.2, size=(duration, width, height))).astype("float32")
    day_length = np.full((duration, width, height), 12.4, dtype="float32")

    soil_shape = (width, height)
    soil_dims = ("x", "y")
    data = xr.Dataset(
        data_vars={
            "rain": (dims, rain, {"units": "mm", "long_name": "rainfall"}),
            "tpMoy": (dims, tp_moy, {"units": "degC", "long_name": "mean temperature"}),
            "rg": (dims, rg, {"units": "MJ/m2", "long_name": "solar radiation"}),
            "ET0": (dims, et0, {"units": "mm", "long_name": "reference evapotranspiration"}),
            "dureeDuJour": (dims, day_length, {"units": "h", "long_name": "day length"}),
            "ru": (soil_dims, np.full(soil_shape, 150.0, dtype="float32"), {"units": "mm/m"}),
            "epaisseurSurf": (soil_dims, np.full(soil_shape, 200.0, dtype="float32")),
            "epaisseurProf": (soil_dims, np.full(soil_shape, 1400.0, dtype="float32")),
            "profRu": (soil_dims, np.full(soil_shape, 1600.0, dtype="float32")),
            "stockIniProf": (soil_dims, np.full(soil_shape, 30.0, dtype="float32")),
            "stockIniSurf": (soil_dims, np.full(soil_shape, 0.0, dtype="float32")),
            "runoff_threshold": (soil_dims, np.full(soil_shape, 25.0, dtype="float32")),
            "runoff_rate": (soil_dims, np.full(soil_shape, 0.08, dtype="float32")),
        },
        coords=coords,
        attrs={"source": "synthetic regression inputs"},
    )
    return data


def build_initialized_simulation(duration=45, width=8, height=7, seed=1234):
    date_start = dt.date(2020, 5, 1)
    param_variety = sample_variety_params()
    param_itk = sample_itk_params(date_start)
    param_soil = sample_soil_params()

    data = build_input_dataset(duration=duration, width=width, height=height, seed=seed)
    data = initialize_simulation(
        data,
        width,
        height,
        duration,
        param_variety,
        param_itk,
        date_start,
    )
    data = initialize_default_irrigation(data)
    data = calculate_once_daily_thermal_time(data, param_variety)
    return data, param_variety, param_itk, param_soil


def assert_equivalent_outputs(reference, candidate, rtol=1e-6, atol=1e-6):
    assert isinstance(candidate, xr.Dataset)
    assert dict(reference.sizes) == dict(candidate.sizes)
    assert set(reference.coords) == set(candidate.coords)
    assert set(reference.data_vars) == set(candidate.data_vars)
    assert reference.attrs == candidate.attrs

    for coord_name in reference.coords:
        np.testing.assert_array_equal(reference.coords[coord_name], candidate.coords[coord_name])

    for name in reference.data_vars:
        assert reference[name].dims == candidate[name].dims
        assert reference[name].attrs == candidate[name].attrs
        np.testing.assert_allclose(
            reference[name].values,
            candidate[name].values,
            rtol=rtol,
            atol=atol,
            equal_nan=True,
        )
