<img src="./fermo_gui/fermo_gui/static/images/Fermo_logo_blue.svg" style="max-width: 50vw;"/>

[![DOI](https://zenodo.org/badge/580868123.svg)](https://doi.org/10.5281/zenodo.7565700)

`fermo_gui` is the graphical user interface for the metabolomics data analysis pipeline [`fermo_core`](https://github.com/fermo-metabolomics/fermo_core). It allows to start new analysis jobs, load existing session files, and visualize results.

For more information about *FERMO*, `fermo_gui`, or `fermo_core`, see the [Documentation](https://fermo-metabolomics.github.io/fermo_docs/).

*Nota bene*: `fermo_gui` has only been tested on Linux systems. While the Docker-installation is likely to work on other systems as well, they are not officially supported. See [*Fermo Online*](https://fermo.bioinformatics.nl/) for a user-friendly installation-free version.

Table of Contents
-----------------
- [Installation and Quickstart](#installation-and-quickstart)
- [Usage](#usage)
- [Attribution](#attribution)
- [For Developers](#for-developers)
- [Contributing](#contributing)

## Installation and Quickstart

### With docker from GitHub

- Install `docker` and `docker-compose`
- Download or clone the [repository](https://github.com/fermo-metabolomics/fermo)
- (Change into the fermo_gui base directory if not already present)
- Run `docker-compose up --build`. This will compose the docker container, install all dependencies and start the application.
- Open the application in any browser with the URL `http://0.0.0.0:8001/`
- To terminate the container, simply hit `ctrl+c`

## Usage

For more information about *FERMO*, `fermo_gui`, or `fermo_core`, see the [Documentation](https://fermo-metabolomics.github.io/fermo_docs/).

## Note for running offline

*The [cleanup_jobs.py](fermo_gui/cleanup_jobs.py) deletes jos older than 30 days and is automatically started by the [entrypoint_docker.sh](fermo_gui/entrypoint_docker.sh) script. If necessary, disable manually.

### Publications

See [FERMO online](https://fermo.bioinformatics.nl/) for information on citing `fermo_gui`.

## For Developers

### Dependencies

A list of dependencies can be found in the file [pyproject.toml](fermo_gui/pyproject.toml).

### Installation and Setup

- Clone the repository to your local machine and enter the `fermo_gui` [source directory](fermo_gui/)
- Install `uv` as described [here](https://docs.astral.sh/uv/getting-started/installation/)
- Run `uv sync` to install dependencies in a virtual environment
- Install redis-server with `sudo apt-get install redis-server`
- Run the app with `uv run flask --app fermo_gui run --debug`
- In a separate command line window, run `uv run celery -A make_celery worker --loglevel ERROR`

### Config file

The flask application automatically reads configuration settings from a `config.py` file in the `instance` directory in the `fermo_gui` [source directory](fermo_gui/) (not in version control for security reasons). 
If not available, `fermo_gui` will employ default settings, assuming that the application runs offline. 
These default settings must not be used if the application is to be deployed to production. 
The following default settings are used:

```python config.py
SECRET_KEY: str # Security
ONLINE: bool = True # Flag for online/offline functionality
CELERY: dict = {
    "broker_url": "redis://localhost",
    "result_backend": "redis://localhost",
    "task_ignore_result": True,
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
