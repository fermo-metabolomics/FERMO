<img src="./fermo_gui/fermo_gui/static/images/Fermo_logo_blue.svg" style="max-width: 50vw;"/>

[![DOI](https://zenodo.org/badge/580868123.svg)](https://doi.org/10.5281/zenodo.7565700)

Contents
-----------------
- [Overview](#overview)
- [Documentation](#documentation)
- [System Requirements](#system-requirements)
- [Installation Guide](#installation-guide)
- [Quick Start](#quick-start)
- [Demo](#demo)
- [Attribution](#attribution)
- [For Developers](#for-developers)


## Overview

FERMO is a dashboard for metabolomics data analysis. 
FERMO integrates metabolomics data with orthogonal data such as phenotype information for rapid, hypothesis-driven prioritization.
To perform data anlysis, FERMO utilizes the [fermo_core](https://github.com/fermo-metabolomics/fermo_core) package.

FERMO can be freely accessed online at [*FERMO Online*](https://fermo.bioinformatics.nl/). For a local installation, see the description below.

For general information on FERMO, see the [FERMO Metabolomics GitHub Organization](https://github.com/fermo-metabolomics) page.

## Documentation

The official documentation can be found [HERE](https://fermo-metabolomics.github.io/fermo_docs/).

## System Requirements

### Hardware requirements

`fermo_core` can be run on a standard computer and does not have any special requirements.

### Software requirements

#### OS Requirements

Local installation of this package is only supported for Linux (tested on Ubuntu 20.04 and 22.04).

#### Python dependencies

Dependencies including exact versions are specified in the [pyproject.toml](./fermo_gui/pyproject.toml) file.

## Installation Guide

Building the Docker-container should take no more than a few minutes.

*Note: the Docker-container automatically runs the script [cleanup_jobs.py](fermo_gui/cleanup_jobs.py), which automatically deletes jobs older than 30 days. If you plan to run the container for a long time, you need to disable this in [entrypoint_docker.sh](fermo_gui/entrypoint_docker.sh).*

### With `docker` from GitHub

*Assumes that you have `docker` installed on your machine*

```commandline
docker build -t fermo_gui .
docker run -p 8001:8001 fermo_gui
```


### With `docker-compose` from GitHub

*Assumes that you have `git`, `docker` and `docker-compose` installed on your machine.*

```commandline
git clone git@github.com:fermo-metabolomics/FERMO.git
cd FERMO
docker-compose up --build
```

Once started, FERMO can be accessed in any browser at the URL [http://0.0.0.0:8001/](http://0.0.0.0:8001/).



## Quick Start

### Running FERMO on your data

For an installation-free version, please see [*FERMO Online*](https://fermo.bioinformatics.nl/)

As minimal requirement, FERMO takes LC-MS(/MS) metabolomics data, which it can integrate with a range of optional orthogonal data formats.
Compatible formats are described in the [Documentation](https://fermo-metabolomics.github.io/fermo_docs/home/input_output/).

For a step-by-step guide, please refer to our [Documentation](https://fermo-metabolomics.github.io/fermo_docs/home/gui.overview/).

## Demo

### Overview

To demonstrate the functionality of FERMO, we provide an [example dataset](./example_data) sourced from [this publication](https://doi.org/10.1021/acs.jnatprod.0c00807).
It describes a set of extracts from strains belonging to the bacterial genus *Planomonospora* grown in the same condition, showing differential antibiotic activity against *Staphylococcus aureus*.
FERMO can be used to investigate and prioritize the phenotype-associated and differentially abundant molecular features.
Application of the `Phenotype Score` filter setting on the dashboard results in the selection of a group of molecular features annotated as siomycins, thiopeptides with known anti-Gram positive antibiotic activity.

Details on the experimental conditions can be found in the [Wiki](https://github.com/fermo-metabolomics/fermo_core/wiki/Demo-example-files-methods).

### Setup and start analysis

The analysis can be started on the `Start of Load Analysis` page. We recommend using [*FERMO Online*](https://fermo.bioinformatics.nl/), but the app can be also started locally.

First, load the example files in the corresponding fields.

- Peak table file parameters : [case_study_peak_table_quant_full.csv](./example_data/case_study_peak_table_quant_full.csv)
- MS/MS file parameters: [case_study_MSMS.mgf](./example_data/case_study_MSMS.mgf)
- Phenotype data file parameters: [case_study_bioactivity_qualitative.csv](./example_data/case_study_bioactivity_qualitative.csv)
- Sample metadata file parameters: [case_study_group_metadata.csv](./example_data/case_study_group_metadata.csv)
- Feature identity annotation parameters/MS2Query Annotation Module: [case_study.ms2query_results.csv](./example_data/case_study.ms2query_results.csv)

All settings can be left default except in *Phenotype data file parameters*. 
Here, the format of the phenotype data file must be specified as `Qualitative`.

Once all files and parameters are specified, the analysis is initiated by clicking on the `Start new analysis` button.

Execution time is hardware-dependent but usually takes only a few minutes. 
On a machine running Ubuntu 22.04 with Intel® Core™ i5-7200U CPU @ 2.50GHz x 4 with 8 GiB Memory, execution time was 104 seconds.

### Results and Interpretation

After successful completion of the run, the GUI will guide you to the dashboard page showing the results.

By using the `Search and filter options` panel and selecting `Show additional filters`, the `Phenotype score filter` can be applied.

Antibiotic activity is attributable to the thiopeptide siomycin and congeners (e.g. feature ID `83`).

## Attribution

### License

FERMO is an open source tool licensed under the MIT license (see [LICENSE](LICENSE.md)).

### Publications

See [CITATION.cff](CITATION.cff) or [FERMO online](https://fermo.bioinformatics.nl/) for information on citing FERMO.


## For Developers

*Nota bene: for details on how to contribute to the FERMO project, please refer to [CONTRIBUTING](CONTRIBUTING.md).*

### Package Installation

*Please note that the development installation is only tested and supported on (Ubuntu) Linux.*

#### With `uv` from GitHub

*Note: assumes that `uv` and `redis-server` are installed locally*

```commandline
git clone git@github.com:fermo-metabolomics/FERMO.git && cd FERMO
uv sync
uv run flask --app fermo_gui run --debug
```

In a separate terminal, run `celery`
```commandline
uv run celery -A make_celery worker --loglevel ERROR
```

#### With `docker-compose` from GitHub

*Note: assumes that `docker-compose` is installed locally and can be accessed without `sudo`*

```commandline
git clone git@github.com:fermo-metabolomics/FERMO.git && cd FERMO
docker-compose build --no-cache
docker-compose up -d
```

### Config file

The FERMO Flask application runs by default in "offline" mode, which does not set restrictions in files sizes used. 
To run FERMO in "online" (production-ready) mode, the default settings need to be overridden by a `config.py` file in an `instance` directory in the `fermo_gui` [source directory](fermo_gui).

**WARNING: DO NOT USE DEFAULT SETTINGS IN PRODUCTION!**

```python config.py
SECRET_KEY: str # Security
ONLINE: bool = True # Flag for online/offline functionality
CELERY: dict = {
    "broker_url": "redis://localhost",
    "result_backend": "redis://localhost",
    "task_soft_time_limit": 3600
} # settings for async job handling
ROOTURL = "fermo" # subdomain, only used for email
MAIL_DEFAULT_SENDER: str # settings for postgres mail
MAIL_SERVER: str
MAIL_PORT: int
MAIL_USE_TLS: bool
MAIL_USE_SSL: bool
```

The number of workers can be adjusted in the [`entrypoint_docker.sh`](fermo_gui/entrypoint_docker.sh) script.

### FERMO Online update procedure

```commandline
docker cp fermo-fermo_gui-1:/fermo_gui/fermo_gui/upload .
docker-commpose stop
git pull
docker-compose build --no-cache
docker-compose up -d
docker cp ./upload fermo-fermo_gui-1:/fermo_gui/fermo_gui/
docker exec fermo-fermo_gui-1 ls fermo_gui/upload | wc -l
```