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

This package will work with Python >3.8.x.

Clone this repository and navigate to the directory:

    git clone https://github.com/SARRA-cropmodels/SARRA-Py/
    cd SARRA-Py

(optional) set up and activate a virtual environment for a clean installation of dependencies:

```bash
conda create --name sarra_py python=3.9
conda activate sarra_py
conda install pip
pip install -r requirements.txt
```

Install **sarra_py** package and its dependencies with pip:
    
    pip install .

## Usage

This package is provided with a set of Jupyter notebooks to illustrate its use. You can find them in the `notebooks` folder (to use it you can install jupyter `pip install jupyterlab` and run it `jupyter-lab`. Do not forget to switch to a IPython kernel calling for your virtual environment if created.

## Documentation

The documentation is available at [https://sarra-cropmodels.github.io/SARRA-Py/](https://sarra-cropmodels.github.io/SARRA-Py/).

## Contributing

Please read [CONTRIBUTING.md](https://github.com/SARRA-cropmodels/SARRA-Py/blob/main/CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Support

If you have any questions, feel free to [post an issue in our GitHub repo](https://github.com/SARRA-cropmodels/SARRA-Py/issues).

## License

This project is licensed under the GNU GPLv3 license - see the [LICENSE](https://github.com/SARRA-cropmodels/SARRA-Py/blob/main/LICENSE) file for details.

## Publications

If you use SARRA-Py in your research, please cite the following publication:

- [SARRA-Py: A Python-based crop simulation model for regional-scale analysis](https://doi.org/10.1016/j.softx.2025.102145). *SoftwareX*, 2025. DOI: [10.1016/j.softx.2025.102145](https://doi.org/10.1016/j.softx.2025.102145)
