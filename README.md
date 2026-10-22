# SARRA-Py

SARRA-Py is a crop simulation model implemented in Python from the SARRA family of models ([SARRA-H](https://github.com/SARRA-cropmodels/SARRA-H), [SARRA-O](https://github.com/SARRA-cropmodels/SARRA-O)).

SARRA-Py has the same philosophy than the rest of the SARRA family of models : a daily time step, simple dynamic hydrological balance model, used to estimate the impact of climate scenarios on annual crops, assuming that crop performance is a function of the accumulated hydrological constraints during the crop's growth cycle. 

SARRA-Py formalisms are based on those of its predecessors. Its main difference with SARRA-H is that SARRA-Py is spatialized, performing its calculations on a georeferenced grid. In that, it is much comparable with SARRA-O, however its Python implementation and its use of xarray architecture facilitates articulation with data formats and tools used in remote sensing and weather data analysis.

SARRA-Py integrates tools to facilitate regional scale analyses. We aim its code and formalisms to be open and evolutive, recognizing that any new scientific application may require some adaptation of the tool. SARRA-Py package is provided with notebook examples to illustrate multiple use cases.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Support](#support)
- [License](#license)
- [Publications](#publications)

### Installation

These instructions will get you a copy of the project up and running on your machine.

Version **0.2.0** requires Python 3.8 or newer. The release verification uses
Python 3.12; other supported interpreter versions have not been retested.

Clone this repository and navigate to the directory:

    git clone https://github.com/SARRA-cropmodels/SARRA-Py/
    cd SARRA-Py

Set up and activate a virtual environment, then install the package and its
core dependencies:

```bash
conda create --name sarra_py python=3.12
conda activate sarra_py
python -m pip install .
```

For the example notebooks, install the additional notebook environment:

```bash
python -m pip install ".[notebooks]"
```

The core installation covers the simulation API, CLI, data loaders and Dask.
The optional group adds Jupyter and the analysis, mapping and calibration
libraries imported by the example notebooks. Notebook files are in this
repository; their datasets are downloaded or prepared as described in each
example. The current verification environment uses Python 3.12.3.

## Usage

After installing `.[notebooks]`, run `jupyter lab` and open an example from the
`notebooks` folder. Select the kernel belonging to the environment where
SARRA-Py was installed.

Run the notebooks from the `notebooks/` directory. See the [example notebook guide](docs/notebook_examples.md) for workflows, data availability and scenario runs through the public API.

## Python API and CLI

A simulation can be run through the validated Python API or with a YAML file:

```bash
sarra-py run.yaml
# or: python -m sarra_py run.yaml
sarra-py --version
```

The CLI accepts a prepared NetCDF dataset or date-coded TAMSAT/AgERA5
GeoTIFF directories plus a soil NetCDF on the rainfall grid. See the
[API and CLI guide](docs/usage_api_cli.md), [parameter files](docs/parameter_files.md)
and [architecture](docs/architecture.md) for configuration and input requirements.

## Documentation

The Markdown files in [`docs/`](docs/README.md) are the maintained documentation.
Start with the [model formalisms](docs/model_formalisms.md) for the daily equations
and their validation status. The [API and CLI guide](docs/usage_api_cli.md),
[parameter guide](docs/parameter_files.md), [notebook guide](docs/notebook_examples.md)
and [spatialization strategy](docs/spatialization_strategy.md) cover practical use.
Keep these Markdown files in sync with changes to the model or API.
See the [changelog](CHANGELOG.md) for release changes.

## Contributing

Please read [CONTRIBUTING.md](https://github.com/SARRA-cropmodels/SARRA-Py/blob/main/CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Support

If you have any questions, feel free to [post an issue in our GitHub repo](https://github.com/SARRA-cropmodels/SARRA-Py/issues).

## License

This project is licensed under the GNU GPLv3 license - see the [LICENCE](LICENCE) file for details.

## Publications

If you use SARRA-Py in your research, please cite the following publication:

- [SARRA-Py: A Python-based crop simulation model for regional-scale analysis](https://doi.org/10.1016/j.softx.2025.102145). *SoftwareX*, 2025. DOI: [10.1016/j.softx.2025.102145](https://doi.org/10.1016/j.softx.2025.102145)
