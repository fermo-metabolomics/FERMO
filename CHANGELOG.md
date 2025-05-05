# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.1.0] - 2025-05-05

### Added

- Added additional examples
- Added support for mzmine4 and antismash8
- Implemented download page for large sessions

### Changed

- Changed install build from `hatch` to `uv`
- Reworked Start Analysis page
- Reworked all frontend pages
- Moved from wtforms to native html forms
- Reworked job dispatching and running
- Moved repo to fermo-metabolomics GitHub page

### Fixed

- Updated documentation links
- Updated dependency versions (nginx, fermo_core)
- Fixed dashboard bugs
- Fixed nginx vulnerability

## [1.0.9] - 2024-07-24

### Fixed

- Fixed increase of version of `fermo_core` to `0.4.3`

## [1.0.8] - 2024-07-23

### Changed

- Bumped version of `fermo_core` to `0.4.3`

## [1.0.7] - 2024-07-10

### Added

- Example: added example result files for download

### Fixed

- Job URLs: when job was started after loading old parameters, result URL was malformed
- Nginx config: fixed default upload file size
- Dashboard: clarified download field names

## [1.0.6] - 2024-06-19

### Fixed

- Fixed broken redirect for 'job_not_found'

## [1.0.5] - 2024-06-19

### Changed

- Updated html templates

## [1.0.4] - 2024-06-18

### Fixed

- Fixed required flag for Chrome and Edge Plotly rendering

## [1.0.3] - 2024-06-18

### Fixed

- Additional fixing of malformed link in notification email

## [1.0.2] - 2024-06-18

### Fixed

- Fixed malformed link in notification email

## [1.0.1] - 2024-06-18

### Fixed

- Added 'restart' flags to docker-compose services for increased maintainability

## [1.0.0] - 2024-06-16

### Changed

- Full rework of frontend and backend of fermo_gui
- Use of fermo_core as processing backend
- [Breaking Change] No compatibility with previous versions of FERMO

## [0.9.1] - 2024-01-22

### Changed

- Full rework on fermo frontend and backend
- Replaced legacy code with Flask application

## [0.8.11] - 2023-04-16

### Added

- Re-introduced support for macOS
- Startup script for macOS

### Changed

- Updated to MS2Query v 0.7.3.2 (by Niek de Jonge)

## [0.8.10] - 2023-02-14

### Fixed

- Bugfix of `modify_feature_info_df()` in  `dashboard_functions.py`

## [0.8.9] - 2023-02-10

### Added

- Tracking of changes with CHANGELOG.md

### Changed

- Changed relative module import paths to absolute ones, making installation of tool via `pip install -e .` mandatory

### Fixed

- Bugfix by modifying `requirements.txt`: specifying package `matchmsextras==0.3.0`

## [0.8.8] - 2023-01-24

### Added

- Expanded adduct detection functionality - FERMO now also recognizes `[M+NH4]+`, `[M+K]+`, `[M+H2O+H]+`, `[M-H2O+H]+` (0.8.8.3)

### Changed

- Rework of fold-change filter on dashboard page: a range, and groups to be excluded or included can be specified (0.8.8.1)
- Changed handling of webbrowser opening (0.8.8.2)

## [0.8.7] - 2023-01-15

### Added:

- Installation via `pip install .` using `pyproject.toml`
- Centralization of dependency metadata in `requirements.txt`
- Bibliographic information using `CITATION.cff`
- Initialization of testing via `pytest` package
- Coverage of `calculate_feature_overlap.py` with unit tests
- Build testing with GitHub actions workflow `.github/workflows/CI_build.yml`

### Changed:

- Changed directory structure: moved source code to `src/fermo/...`
- Rewrite of `calculate_feature_overlap.py` to allow for testing and increase maintainability

## [0.8.6] - 2022-12-25

### Fixed:

- Bugfix in quantitative biological data parsing related to issue [Cannot upload quantitative biological data (*.csv) file](https://github.com/fermo-metabolomics/FERMO/issues/1)

## [0.8.5] - 2022-12-23

### Added:

- Initial public version of FERMO
