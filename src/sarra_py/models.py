from .bilan_pheno import *
from .bilan_carbo import *
from .bilan_hydro import *
from .data_preparation import *

import numpy as np
import xarray as xr
from tqdm import tqdm as tqdm


def _normalize_engine(engine):
    """Return the canonical execution engine name.

    Parameters
    ----------
    engine : str
        Public engine selector passed to :func:`run_model` or
        :func:`run_waterbalance_model`. Accepted aliases are ``"numpy"``,
        ``"np"``, ``"fast"``, ``"xarray"``, and ``"legacy"``.

    Returns
    -------
    str
        Either ``"numpy"`` or ``"xarray"``.

    Raises
    ------
    ValueError
        If ``engine`` does not name a supported engine.

    Notes
    -----
    This helper only normalizes the selector. It does not change the default
    public API, which remains ``engine="xarray"`` in the public model
    functions.
    """
    if engine in ("numpy", "np", "fast"):
        return "numpy"
    if engine in ("xarray", "legacy"):
        return "xarray"
    raise ValueError("engine must be 'numpy' or 'xarray'")


def _dataset_to_numpy_state(data):
    """Extract model variables from an xarray dataset as NumPy arrays.

    Parameters
    ----------
    data : xarray.Dataset
        Initialized SARRA-Py simulation dataset. Data variables are expected to
        use the notebook-facing dimensions, usually ``("time", "x", "y")``
        for daily rasters and ``("x", "y")`` for static rasters.

    Returns
    -------
    dict[str, numpy.ndarray]
        Mapping from data variable names to NumPy arrays. Read-only arrays are
        copied so that the daily model loop can update them in place.

    Side Effects
    ------------
    Does not add or remove xarray variables. Returned arrays may share memory
    with ``data`` when the source xarray storage is writable.

    Notes
    -----
    The NumPy engine keeps all agronomic calls unchanged and swaps only the
    container used inside the daily loop.
    """
    state = {}

    for name, variable in data.data_vars.items():
        values = np.asarray(variable.values)
        if not values.flags.writeable:
            values = values.copy()
        state[name] = values

    return state


def _restore_numpy_state(data, state):
    """Write a NumPy-backed model state back into an xarray dataset.

    Parameters
    ----------
    data : xarray.Dataset
        Original dataset passed to the public API. It provides dimensions,
        coordinates, attributes, and existing variable metadata.
    state : dict[str, numpy.ndarray]
        Model state produced by a NumPy execution loop.

    Returns
    -------
    xarray.Dataset
        The same dataset object, with data variables updated from ``state``.

    Side Effects
    ------------
    Mutates ``data`` in place. Existing variables keep their xarray variable
    objects and attributes; new variables are inserted with dimensions inferred
    from their shapes.

    Notes
    -----
    This helper is the boundary where ``engine="numpy"`` reconstructs the
    notebook-facing xarray output. It does not alter coordinates or dataset
    attributes.
    """
    for name, values in state.items():
        if name in data:
            data[name].data = values
        else:
            data[name] = (_infer_dims_from_shape(data, values.shape), values)

    return data


def _infer_dims_from_shape(data, shape):
    """Infer xarray dimensions for a new array shape.

    Parameters
    ----------
    data : xarray.Dataset
        Dataset used as the dimension reference.
    shape : tuple[int, ...]
        Shape of the NumPy array to restore.

    Returns
    -------
    tuple[str, ...]
        Dimension names matching ``shape``.

    Raises
    ------
    ValueError
        If no existing variable or rainfall-based convention matches the
        supplied shape.

    Notes
    -----
    The primary convention is ``rain.dims`` for daily rasters and
    ``rain.dims[1:]`` for static rasters.
    """
    if "rain" in data:
        rain = data["rain"]
        if shape == rain.shape:
            return rain.dims
        if len(shape) == len(rain.shape) - 1 and shape == rain.shape[1:]:
            return rain.dims[1:]

    for variable in data.data_vars.values():
        if shape == variable.shape:
            return variable.dims

    raise ValueError(f"Cannot infer xarray dimensions for array shape {shape}")


def _run_loop(iterator, data, paramVariete, paramITK, paramTypeSol):
    """Execute the full SARRA-Py daily model sequence.

    Parameters
    ----------
    iterator : iterable of int
        Daily time-step indices to execute.
    data : xarray.Dataset or dict[str, numpy.ndarray]
        Initialized model state. The xarray engine passes a dataset; the NumPy
        engine passes a variable-to-array mapping with the same variable names.
    paramVariete, paramITK, paramTypeSol : dict
        Variety, management, and soil parameter dictionaries used by the
        existing agronomic functions.

    Returns
    -------
    xarray.Dataset or dict[str, numpy.ndarray]
        Updated model state in the same container type as ``data``.

    Side Effects
    ------------
    Mutates ``data`` through the called daily functions. Expected daily raster
    dimensions are those already present on the initialized input, typically
    ``("time", "x", "y")``.

    Notes
    -----
    This function intentionally preserves the historical ordering of
    phenology, water balance, carbon balance, and yield updates.
    """
    for j in iterator:

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


def _run_waterbalance_loop(iterator, data, paramVariete, paramITK, paramTypeSol):
    """Execute the water-balance-oriented daily model sequence.

    Parameters
    ----------
    iterator : iterable of int
        Daily time-step indices to execute.
    data : xarray.Dataset or dict[str, numpy.ndarray]
        Initialized model state for either the xarray or NumPy engine.
    paramVariete, paramITK, paramTypeSol : dict
        Variety, management, and soil parameter dictionaries.

    Returns
    -------
    xarray.Dataset or dict[str, numpy.ndarray]
        Updated model state in the same container type as ``data``.

    Side Effects
    ------------
    Mutates ``data`` through the daily thermal-time, phenology, water balance,
    and limited carbon-balance updates used by this model variant.

    Notes
    -----
    ``paramTypeSol`` is kept in the signature for compatibility with the
    public model call and the full loop, even when the current loop body does
    not read it directly.
    """
    for j in iterator:

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


def _make_iterator(duration, progress):
    """Build the daily iterator used by model loops.

    Parameters
    ----------
    duration : int
        Number of daily time steps to execute.
    progress : bool
        If ``True``, wrap the range in ``tqdm`` for notebook progress display.

    Returns
    -------
    range or tqdm
        Iterator over integer day indices from ``0`` to ``duration - 1``.

    Notes
    -----
    This helper only controls display. It does not affect model state or
    numerical results.
    """
    days = range(duration)
    if progress:
        return tqdm(days)
    return days


def _run_with_engine(loop, paramVariete, paramITK, paramTypeSol, data, duration, engine, progress):
    """Dispatch a public model call to the xarray or NumPy engine.

    Parameters
    ----------
    loop : callable
        Internal daily loop, such as ``_run_loop`` or
        ``_run_waterbalance_loop``.
    paramVariete, paramITK, paramTypeSol : dict
        Variety, management, and soil parameter dictionaries.
    data : xarray.Dataset or mapping
        Initialized model state. Notebook workflows normally pass an
        ``xarray.Dataset``.
    duration : int
        Number of daily time steps to execute.
    engine : {"xarray", "numpy", "legacy", "np", "fast"}
        Execution backend selector. ``"xarray"`` keeps the historical
        container throughout the daily loop. ``"numpy"`` converts variables to
        arrays before the loop and restores an xarray dataset afterwards.
    progress : bool
        Whether to display a tqdm progress bar.

    Returns
    -------
    xarray.Dataset or mapping
        Updated model state. For notebook-style xarray input, both engines
        return an xarray dataset.

    Side Effects
    ------------
    Mutates ``data`` in place, matching the historical API behavior.
    """
    engine = _normalize_engine(engine)
    iterator = _make_iterator(duration, progress)

    if engine == "xarray" or not isinstance(data, xr.Dataset):
        return loop(iterator, data, paramVariete, paramITK, paramTypeSol)

    state = _dataset_to_numpy_state(data)
    state = loop(iterator, state, paramVariete, paramITK, paramTypeSol)
    return _restore_numpy_state(data, state)


def run_model(paramVariete, paramITK, paramTypeSol, data, duration, engine="xarray", progress=True):
    """Run the full daily SARRA-Py crop simulation.

    Parameters
    ----------
    paramVariete : dict
        Variety parameters used by phenology, carbon-balance, water-balance,
        and yield functions.
    paramITK : dict
        Management parameters, including sowing and irrigation settings.
    paramTypeSol : dict
        Soil parameter dictionary kept for API compatibility and for functions
        that use soil settings.
    data : xarray.Dataset
        Initialized model dataset, usually produced by
        ``initialize_simulation`` and related notebook helpers. Daily variables
        are expected to share the rainfall dimensions, typically
        ``("time", "x", "y")``. Static grid variables usually use
        ``("x", "y")``.
    duration : int
        Number of daily time steps to simulate.
    engine : {"xarray", "numpy"}, default "xarray"
        Execution backend. ``"xarray"`` is the historical public default.
        ``"numpy"`` is an opt-in internal acceleration path that converts data
        variables to NumPy arrays for the daily loop and reconstructs xarray
        outputs before returning.
    progress : bool, default True
        Whether to display a tqdm progress bar.

    Returns
    -------
    xarray.Dataset
        The updated simulation dataset with the same public xarray-oriented
        API surface as the input workflow.

    Side Effects
    ------------
    Mutates ``data`` in place by updating daily model variables such as
    phenology, water balance, biomass, and yield variables. Coordinates and
    existing variable names are preserved by the public workflow.

    Notes
    -----
    This function is adapted from the procedure sequence of the SARRA-H v42
    model. The engine selector changes only the internal container used during
    execution; it is not intended to change agronomic logic.
    """
    return _run_with_engine(
        _run_loop,
        paramVariete,
        paramITK,
        paramTypeSol,
        data,
        duration,
        engine,
        progress,
    )



def run_waterbalance_model(paramVariete, paramITK, paramTypeSol, data, duration, engine="xarray", progress=True):
    """Run the daily SARRA-Py water-balance model variant.

    Parameters
    ----------
    paramVariete : dict
        Variety parameters required by thermal-time, phenology, transpiration,
        and related helper functions.
    paramITK : dict
        Management parameters, including sowing and irrigation settings.
    paramTypeSol : dict
        Soil parameter dictionary retained for compatibility with the full
        model API.
    data : xarray.Dataset
        Initialized simulation dataset. Daily variables are expected to share
        rainfall dimensions, typically ``("time", "x", "y")``; static grid
        variables usually use ``("x", "y")``.
    duration : int
        Number of daily time steps to simulate.
    engine : {"xarray", "numpy"}, default "xarray"
        Execution backend. ``"xarray"`` keeps the historical public behavior.
        ``"numpy"`` converts variables to NumPy arrays internally and restores
        an xarray dataset before returning.
    progress : bool, default True
        Whether to display a tqdm progress bar.

    Returns
    -------
    xarray.Dataset
        Updated simulation dataset.

    Side Effects
    ------------
    Mutates ``data`` in place by updating thermal-time, phenology,
    water-balance, and the subset of carbon-balance variables used by this
    model variant.

    Notes
    -----
    The engine selector is an execution detail. The public default remains
    ``engine="xarray"`` for backward compatibility with notebooks.
    """
    return _run_with_engine(
        _run_waterbalance_loop,
        paramVariete,
        paramITK,
        paramTypeSol,
        data,
        duration,
        engine,
        progress,
    )
