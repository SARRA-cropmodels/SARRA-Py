import warnings

import numpy as np
import xarray as xr

from sarra_py.bilan_carbo import estimate_critical_nitrogen_concentration


def test_ncrit_is_undefined_without_positive_biomass():
    biomass = np.array([[[0.0, 1000.0, 2500.0, -1.0, np.nan]]])
    data = xr.Dataset(
        {
            "biomasseTotale": (("time", "y", "x"), biomass.copy()),
            "Ncrit": (("time", "y", "x"), np.zeros_like(biomass)),
        }
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        result = estimate_critical_nitrogen_concentration(0, data)

    actual = result["Ncrit"].values[0, 0]
    assert np.isnan(actual[[0, 3, 4]]).all()
    np.testing.assert_allclose(actual[[1, 2]], 5.35 * np.array([1.0, 2.5]) ** (-0.44))
    np.testing.assert_array_equal(result["biomasseTotale"].values, biomass)
