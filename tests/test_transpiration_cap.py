import numpy as np
import pytest
import xarray as xr

from sarra_py.bilan_hydro import (
    subtract_transpiration_from_root_tank_stock,
    update_plant_transpiration,
)


@pytest.mark.parametrize("container", ["numpy", "xarray"])
def test_transpiration_uses_available_root_water(container):
    demand = np.array([[[5.0, 2.0, 5.0]]])
    stock = np.array([[[3.0, 3.0, 0.0]]])
    if container == "numpy":
        data = {"tr": demand.copy(), "root_tank_stock": stock.copy()}
    else:
        data = xr.Dataset({
            "tr": (("time", "y", "x"), demand.copy()),
            "root_tank_stock": (("time", "y", "x"), stock.copy()),
        })

    update_plant_transpiration(0, data)
    np.testing.assert_allclose(np.asarray(data["tr"])[0, 0], [3.0, 2.0, 0.0])

    subtract_transpiration_from_root_tank_stock(0, data)
    np.testing.assert_allclose(np.asarray(data["root_tank_stock"])[0, 0], [0.0, 1.0, 0.0])
