"""Functionality for input data parsing

Copyright (c) 2022-present Mitja Maximilian Zdouc, PhD

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json
import logging
import os
import shutil
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema
import pandas as pd
import requests
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from fermo_core.input_output.class_parameter_manager import ParameterManager
from fermo_core.input_output.class_validation_manager import ValidationManager
from fermo_core.input_output.param_handlers import (
    AdductAnnotationParameters,
    AsKcbCosineMatchingParams,
    AsKcbDeepscoreMatchingParams,
    BlankAssignmentParameters,
    FeatureFilteringParameters,
    FragmentAnnParameters,
    GroupFactAssignmentParameters,
    GroupMetadataParameters,
    MS2QueryResultsParameters,
    MsmsParameters,
    NeutralLossParameters,
    PeaktableParameters,
    PhenoQualAssgnParams,
    PhenoQuantConcAssgnParams,
    PhenoQuantPercentAssgnParams,
    PhenotypeParameters,
    SpecLibParameters,
    SpecSimNetworkCosineParameters,
    SpecSimNetworkDeepscoreParameters,
    SpectralLibMatchingCosineParameters,
    SpectralLibMatchingDeepscoreParameters,
)
from fermo_core.main import main
from flask import (
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_mail import Message
from pydantic import BaseModel
from requests.exceptions import Timeout
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from fermo_gui.config.extensions import mail


class JobManager(BaseModel):
    """Manages async jobs

    Attributes:
        params: job run parameters
        email: an optional email for notification
        job_id: the job uuid

    """

    params: dict
    email: str | None = None
    job_id: str

    def email_fail(self):
        """Notify user that job failed"""
        if not current_app.config.get("ONLINE") or not self.email:
            return

        root_url = request.url_root
        root_url.replace(
            "http://thornton", f"https://{current_app.config.get('ROOTURL')}"
        )

        msg = Message()
        msg.recipients = [self.email]
        msg.subject = "FERMO JOB FAILED (NOREPLY)"
        msg.html = render_template(
            "email_failure.html", job_id=self.job_id, root_url=root_url
        )
        mail.send(msg)

    def email_success(self):
        """Notify user that job failed"""
        if not current_app.config.get("ONLINE") or not self.email:
            return

        root_url = request.url_root
        root_url.replace(
            "http://thornton", f"https://{current_app.config.get('ROOTURL')}"
        )

        msg = Message()
        msg.recipients = [self.email]
        msg.subject = "FERMO JOB SUCCESS (NOREPLY)"
        msg.html = render_template(
            "email_success.html", job_id=self.job_id, root_url=root_url
        )
        mail.send(msg)

    def download_antismash_job(self):
        """Download antiSMASH job from antiSMASH website

        Raises:
            ValueError: antiSMASH JobID not found
            RuntimeError: timeout of connection
        """
        as_id = self.params["AsResultsParameters"].get("job_id")
        if not as_id:
            return

        try:
            url = f"https://antismash.secondarymetabolites.org/upload/{as_id}/"
            response = requests.get(url, timeout=5)
            zips = [
                line.split('"')[1]
                for line in response.text.splitlines()
                if ".zip" in line
            ]

            if not zips:
                raise ValueError("antiSMASH JobID not found on antiSMASH server.")
            else:
                for zip_file in zips:
                    response = requests.get(os.path.join(url, zip_file), timeout=120)

                    job_path = current_app.config.get("UPLOAD_FOLDER").joinpath(
                        f"{self.job_id}"
                    )
                    with open(job_path.joinpath(f"{zip_file}"), "wb") as f:
                        f.write(response.content)

                    with zipfile.ZipFile(job_path.joinpath(f"{zip_file}"), "r") as out:
                        out.extractall(job_path.joinpath(f"{zip_file.split('.')[0]}"))

                    if not Path(
                        self.params["AsResultsParameters"].get("directory_path")
                    ).exists():
                        raise FileNotFoundError(
                            "AntiSMASH results were not downloaded in the expected location - TERMINATE"
                        )

                    os.remove(job_path.joinpath(f"{zip_file}"))

        except Timeout as e:
            raise RuntimeError(
                f"Connection to antiSMASH server timed out: {e!s}"
            ) from e

    def configure_logger(self) -> logging.Logger:
        """Set up logging parameters"""
        logger = logging.getLogger("fermo_core")
        logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(
            current_app.config.get("UPLOAD_FOLDER").joinpath(
                f"{self.job_id}/results/out.fermo.log"
            ),
            mode="w",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        logger.addHandler(file_handler)
        return logger

    def run_fermo(self):
        """Run fermo_core on the respective job id

        Raises:
            RuntimeError: fermo_core run failed unexpectedly
        """
        start_time = datetime.now()
        logger = self.configure_logger()
        logger.debug(f"Started 'fermo_core' on job_id '{self.job_id}'.")

        try:
            param_manager = ParameterManager()
            param_manager.assign_parameters_cli(self.params)
            main(param_manager, start_time, logger)
        except Exception as e:
            msg = f"FERMO run failed: {e!s}"
            logger.error(msg)
            raise RuntimeError(msg) from e


@shared_task(ignore_result=False)
def start_job(job_id: str, email: str | None) -> bool:
    """Wrapper to start fermo_core jobs asynchronously.

    Args:
        job_id: the uuid job reference
        email: an email address or None

    Returns: A bool signaling job outcome to Celery
    """
    job_path = Path(f'{current_app.config.get("UPLOAD_FOLDER")}/{job_id}')
    with open(job_path.joinpath(f"{job_id}.parameters.json")) as infile:
        params = json.load(infile)

    def _write_fail_file(m: str):
        with open(job_path.joinpath(f"results/out.failed.txt"), "w") as f:
            f.write(m)

    manager = JobManager(params=params, job_id=job_id, email=email)
    try:
        manager.download_antismash_job()
        manager.run_fermo()
        manager.email_success()
        return True
    except SoftTimeLimitExceeded as e:
        msg = f"Job {job_id} surpassed maximum time limit and was terminated: {e!s}"
        _write_fail_file(msg)
        manager.email_fail()
        raise
    except Exception as e:
        msg = f"Job {job_id} encountered an error and was terminated: {e!s}"
        _write_fail_file(msg)
        manager.email_fail()
        raise


class InputParser(BaseModel):
    """Converts raw user input into parameters file

    Attributes:
        uuid: the job uuid
        data: the user-submitted data
        params: the default params, to be updated
        uploads: the Path to the uploads dir
        sess_schema: Path to the session file JSON Schema
    """

    uuid: str = str(uuid.uuid4())
    data: dict
    params: dict
    uploads: Path
    sess_schema: Path = Path(__file__).parent.parent.joinpath("schema.json")

    def return_error(self) -> str:
        """Default error redirect"""
        return render_template(
            template_name_or_list="forms.html",
            job_id=None,
            online=current_app.config.get("ONLINE"),
            params=self.params,
            max_size=current_app.config.get("MAX_CONTENT_LENGTH") or 0,
        )

    def create_unique_dir(self) -> None:
        """Create unique job dir for file storage"""
        while True:
            path = self.uploads.joinpath(self.uuid)
            if not path.exists():
                path.mkdir()
                path.joinpath("results").mkdir()
                return
            else:
                self.uuid = str(uuid.uuid4())

    @staticmethod
    def update_keys(session: dict) -> dict:
        """Converts legacy parameter keys to current format"""
        mapping = {
            "PhenoQualAssgnParams": "PhenoQualAssgnParameters",
            "PhenoQuantPercentAssgnParams": "PhenoQuantPercentAssgnParameters",
            "PhenoQuantConcAssgnParams": "PhenoQuantConcAssgnParameters",
            "AsKcbCosineMatchingParams": "AsKcbCosineMatchingParameters",
            "AsKcbDeepscoreMatchingParams": "AsKcbDeepscoreMatchingParameters",
        }

        for old, new in mapping.items():
            if old in session.get("parameters"):
                session.get("parameters")[new] = session.get("parameters").pop(old)

        return session

    @staticmethod
    def determine_file_size(f: FileStorage) -> int:
        """Determine the size in bytes

        Args:
            f: A Werkzeug Filestorage object

        Returns:
            The size in bytes as integer
        """
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0)
        return size

    @staticmethod
    def valid_file_size(size: int, name: str) -> None:
        """Check allowed file fize

        Args:
            size: the size in bytes
            name: the file name

        Returns:
            Bool indicating outcome for route handling

        Raises:
            RuntimeError: File empty or exceeding allowed size
        """
        if current_app.config.get("ONLINE") and size > current_app.config.get(
            "MAX_CONTENT_LENGTH"
        ):
            e = (
                f'File {name} is bigger than the allowed '
                f'{current_app.config.get("MAX_CONTENT_LENGTH")} bytes '
                f'(found "{size}" bytes).'
            )
            current_app.logger.error(e)
            flash(e)
            raise RuntimeError(e)

    def check_session_id(self, s_id: str) -> None:
        """Check if job ID exists and sanitize the session file

        Also writes parameters from session file to self

        Args:
            s_id: a FERMO session UID

        Raises:
            FileNotFoundError: session ID not found
            RunTimeError: invalid session file format
        """
        session_path = self.uploads.joinpath(f"{s_id}/results/out.fermo.session.json")
        with open(self.sess_schema) as infile:
            schema = json.load(infile)

        try:
            if session_path.exists():
                with open(session_path) as infile:
                    session = json.load(infile)

                jsonschema.validate(instance=session, schema=schema)
                session = self.update_keys(session)

                for key, val in session.get("parameters").items():
                    if key in self.params:
                        if val.get("activate_module"):
                            self.params[key] = val
                        else:
                            self.params[key]["activate_module"] = False

                with open(session_path, "w") as out:
                    json.dump(session, out, indent=2)
            else:
                raise FileNotFoundError(f"Could not find session ID on server: {s_id}")
        except jsonschema.exceptions.ValidationError as e:
            msg = f"Incorrect FERMO session file formatting: {str(e).splitlines()[0]}"
            raise RuntimeError(msg) from e

    def save_files(self, files: Any):
        """Save the input files

        Args:
            files: a dict of Werkzeug Filestorage ojects

        Raises:
            RuntimeError: issues during file saving

        Notes:
            speclibs must be parsed separately; else, only one speclibfile is stored

        """
        save_path = self.uploads / self.uuid
        save_path_speclib = self.uploads / self.uuid / "spec_lib"

        try:
            speclibs = files.getlist("SpecLibParametersFiles")
            if any(secure_filename(f.filename) for f in speclibs):
                save_path_speclib.mkdir()
                self.params["SpecLibParameters"]["dirpath"] = str(save_path_speclib)
                for file in speclibs:
                    size = self.determine_file_size(file)
                    if size == 0:
                        continue
                    self.valid_file_size(size, secure_filename(file.filename))
                    file.save(
                        save_path_speclib.joinpath(secure_filename(file.filename))
                    )

            for f_id in files:
                file = files.get(f_id)
                size = self.determine_file_size(file)
                if size == 0:
                    continue
                self.valid_file_size(size, secure_filename(file.filename))
                if f_id == "SpecLibParametersFiles":
                    continue
                file.save(save_path.joinpath(secure_filename(file.filename)))
                key = f_id.removesuffix("File")
                self.params[key]["filepath"] = str(
                    save_path.joinpath(secure_filename(file.filename))
                )

        except Exception as e:
            msg = f"An error occurred during the upload file storage: {e!s}"
            raise RuntimeError(msg) from e

    def parse_forms(self):
        """Parse parameters from form fields

        Raises:
            RuntimeError: error occurred during input parsing
        """
        try:
            for key, val in self.data.items():
                match key:
                    case "PeaktableParametersFormat":
                        self.params["PeaktableParameters"]["format"] = str(val)
                    case "PeaktableParametersPolarity":
                        self.params["PeaktableParameters"]["polarity"] = str(val)
                    case "FeatureFilteringParametersActivate":
                        self.params["FeatureFilteringParameters"]["activate_module"] = (
                            val == "on"
                        )
                    case "FeatureFilteringParametersAreaMin":
                        self.params["FeatureFilteringParameters"][
                            "filter_rel_area_range_min"
                        ] = float(val)
                    case "FeatureFilteringParametersAreaMax":
                        self.params["FeatureFilteringParameters"][
                            "filter_rel_area_range_max"
                        ] = float(val)
                    case "FeatureFilteringParametersIntMin":
                        self.params["FeatureFilteringParameters"][
                            "filter_rel_int_range_min"
                        ] = float(val)
                    case "FeatureFilteringParametersIntMax":
                        self.params["FeatureFilteringParameters"][
                            "filter_rel_int_range_max"
                        ] = float(val)
                    case "AdductAnnotationParametersActivate":
                        self.params["AdductAnnotationParameters"]["activate_module"] = (
                            val == "on"
                        )
                    case "AdductAnnotationParametersPpm":
                        self.params["AdductAnnotationParameters"]["mass_dev_ppm"] = (
                            float(val)
                        )
                    case "MsmsParametersFormat":
                        self.params["MsmsParameters"]["format"] = str(val)
                    case "MsmsParametersFormatRelInt":
                        self.params["MsmsParameters"]["rel_int_from"] = float(val)
                    case "NeutralLossParametersActivate":
                        self.params["NeutralLossParameters"]["activate_module"] = (
                            val == "on"
                        )
                    case "NeutralLossParametersPpm":
                        self.params["NeutralLossParameters"]["mass_dev_ppm"] = float(
                            val
                        )
                    case "FragmentAnnParametersActivate":
                        self.params["FragmentAnnParameters"]["activate_module"] = (
                            val == "on"
                        )
                    case "FragmentAnnParametersPpm":
                        self.params["FragmentAnnParameters"]["mass_dev_ppm"] = float(
                            val
                        )
                    case "SpecSimNetworkCosineParametersActivate":
                        self.params["SpecSimNetworkCosineParameters"][
                            "activate_module"
                        ] = val == "on"
                    case "SpecSimNetworkCosineParametersMinNr":
                        self.params["SpecSimNetworkCosineParameters"][
                            "msms_min_frag_nr"
                        ] = int(val)
                    case "SpecSimNetworkCosineParametersTol":
                        self.params["SpecSimNetworkCosineParameters"][
                            "fragment_tol"
                        ] = float(val)
                    case "SpecSimNetworkCosineParametersScore":
                        self.params["SpecSimNetworkCosineParameters"][
                            "score_cutoff"
                        ] = float(val)
                    case "SpecSimNetworkCosineParametersLinks":
                        self.params["SpecSimNetworkCosineParameters"][
                            "max_nr_links"
                        ] = int(val)
                    case "SpecSimNetworkDeepscoreParametersActivate":
                        self.params["SpecSimNetworkDeepscoreParameters"][
                            "activate_module"
                        ] = val == "on"
                    case "SpecSimNetworkDeepscoreParametersMinNr":
                        self.params["SpecSimNetworkDeepscoreParameters"][
                            "msms_min_frag_nr"
                        ] = int(val)
                    case "SpecSimNetworkDeepscoreParametersScore":
                        self.params["SpecSimNetworkDeepscoreParameters"][
                            "score_cutoff"
                        ] = float(val)
                    case "SpecSimNetworkDeepscoreParametersLinks":
                        self.params["SpecSimNetworkDeepscoreParameters"][
                            "max_nr_links"
                        ] = int(val)
                    case "PhenotypeParametersFormat":
                        if val != "false":
                            self.params["PhenotypeParameters"]["format"] = str(val)
                            if val == "qualitative":
                                self.params["PhenoQualAssgnParameters"][
                                    "activate_module"
                                ] = True
                            elif val == "quantitative-percentage":
                                self.params["PhenoQuantPercentAssgnParameters"][
                                    "activate_module"
                                ] = True
                            elif val == "quantitative-concentration":
                                self.params["PhenoQuantConcAssgnParameters"][
                                    "activate_module"
                                ] = True
                            else:
                                raise ValueError(
                                    f"Phenotype file format: '{val}' is not an allowed value"
                                )
                    case "PhenoQualAssgnParametersFactor":
                        self.params["PhenoQualAssgnParameters"]["factor"] = int(val)
                    case "PhenoQualAssgnParametersAlgorithm":
                        self.params["PhenoQualAssgnParameters"]["algorithm"] = str(val)
                    case "PhenoQualAssgnParametersValue":
                        self.params["PhenoQualAssgnParameters"]["value"] = str(val)
                    case "PhenoQuantPercentAssgnParametersAvg":
                        self.params["PhenoQuantPercentAssgnParameters"][
                            "sample_avg"
                        ] = str(val)
                    case "PhenoQuantPercentAssgnParametersVal":
                        self.params["PhenoQuantPercentAssgnParameters"]["value"] = str(
                            val
                        )
                    case "PhenoQuantPercentAssgnParametersAlg":
                        self.params["PhenoQuantPercentAssgnParameters"]["algorithm"] = (
                            str(val)
                        )
                    case "PhenoQuantPercentAssgnParametersFdrAlg":
                        self.params["PhenoQuantPercentAssgnParameters"]["fdr_corr"] = (
                            str(val)
                        )
                    case "PhenoQuantPercentAssgnParametersPVal":
                        self.params["PhenoQuantPercentAssgnParameters"][
                            "p_val_cutoff"
                        ] = float(val)
                    case "PhenoQuantPercentAssgnParametersCoeff":
                        self.params["PhenoQuantPercentAssgnParameters"][
                            "coeff_cutoff"
                        ] = float(val)
                    case "PhenoQuantConcAssgnParametersAvg":
                        self.params["PhenoQuantConcAssgnParameters"]["sample_avg"] = (
                            str(val)
                        )
                    case "PhenoQuantConcAssgnParametersVal":
                        self.params["PhenoQuantConcAssgnParameters"]["value"] = str(val)
                    case "PhenoQuantConcAssgnParametersAlg":
                        self.params["PhenoQuantConcAssgnParameters"]["algorithm"] = str(
                            val
                        )
                    case "PhenoQuantConcAssgnParametersFdrAlg":
                        self.params["PhenoQuantConcAssgnParameters"]["fdr_corr"] = str(
                            val
                        )
                    case "PhenoQuantConcAssgnParametersPVal":
                        self.params["PhenoQuantConcAssgnParameters"]["p_val_cutoff"] = (
                            float(val)
                        )
                    case "PhenoQuantConcAssgnParametersCoeff":
                        self.params["PhenoQuantConcAssgnParameters"]["coeff_cutoff"] = (
                            float(val)
                        )
                    case "GroupMetadataParametersFormat":
                        self.params["GroupMetadataParameters"]["format"] = str(val)
                    case "GroupFactAssignmentParametersActivate":
                        self.params["GroupFactAssignmentParameters"][
                            "activate_module"
                        ] = val == "on"
                    case "GroupFactAssignmentParametersAlgorithm":
                        self.params["GroupFactAssignmentParameters"]["algorithm"] = str(
                            val
                        )
                    case "GroupFactAssignmentParametersValue":
                        self.params["GroupFactAssignmentParameters"]["value"] = str(val)
                    case "BlankAssignmentParametersActivate":
                        self.params["BlankAssignmentParameters"]["activate_module"] = (
                            val == "on"
                        )
                    case "BlankAssignmentParametersFactor":
                        self.params["BlankAssignmentParameters"]["factor"] = int(val)
                    case "BlankAssignmentParametersAlgorithm":
                        self.params["BlankAssignmentParameters"]["algorithm"] = str(val)
                    case "BlankAssignmentParametersValue":
                        self.params["BlankAssignmentParameters"]["value"] = str(val)
                    case "SpecLibParametersFormat":
                        self.params["SpecLibParameters"]["format"] = str(val)
                    case "SpectralLibMatchingCosineParametersActivate":
                        self.params["SpectralLibMatchingCosineParameters"][
                            "activate_module"
                        ] = val == "on"
                    case "SpectralLibMatchingCosineParametersMinMatched":
                        self.params["SpectralLibMatchingCosineParameters"][
                            "min_nr_matched_peaks"
                        ] = int(val)
                    case "SpectralLibMatchingCosineParametersTol":
                        self.params["SpectralLibMatchingCosineParameters"][
                            "fragment_tol"
                        ] = float(val)
                    case "SpectralLibMatchingCosineParametersScore":
                        self.params["SpectralLibMatchingCosineParameters"][
                            "score_cutoff"
                        ] = float(val)
                    case "SpectralLibMatchingCosineParametersDiff":
                        self.params["SpectralLibMatchingCosineParameters"][
                            "max_precursor_mass_diff"
                        ] = int(float(val))
                    case "SpectralLibMatchingDeepscoreParametersActivate":
                        self.params["SpectralLibMatchingDeepscoreParameters"][
                            "activate_module"
                        ] = val == "on"
                    case "SpectralLibMatchingDeepscoreParametersScore":
                        self.params["SpectralLibMatchingDeepscoreParameters"][
                            "score_cutoff"
                        ] = float(val)
                    case "SpectralLibMatchingDeepscoreParametersDiff":
                        self.params["SpectralLibMatchingDeepscoreParameters"][
                            "max_precursor_mass_diff"
                        ] = int(float(val))
                    case "AsResultsParametersJob":
                        if val != "":
                            self.params["AsResultsParameters"]["job_id"] = str(val)
                    case "AsResultsParametersCutoff":
                        self.params["AsResultsParameters"]["similarity_cutoff"] = float(
                            val
                        )
                    case "AsKcbCosineMatchingParametersActivate":
                        self.params["AsKcbCosineMatchingParameters"][
                            "activate_module"
                        ] = val == "on"
                    case "AsKcbCosineMatchingParametersMinMatched":
                        self.params["AsKcbCosineMatchingParameters"][
                            "min_nr_matched_peaks"
                        ] = int(val)
                    case "AsKcbCosineMatchingParametersTol":
                        self.params["AsKcbCosineMatchingParameters"]["fragment_tol"] = (
                            float(val)
                        )
                    case "AsKcbCosineMatchingParametersScore":
                        self.params["AsKcbCosineMatchingParameters"]["score_cutoff"] = (
                            float(val)
                        )
                    case "AsKcbCosineMatchingParametersDiff":
                        self.params["AsKcbCosineMatchingParameters"][
                            "max_precursor_mass_diff"
                        ] = int(float(val))
                    case "AsKcbDeepscoreMatchingParametersActivate":
                        self.params["AsKcbDeepscoreMatchingParameters"][
                            "activate_module"
                        ] = val == "on"
                    case "AsKcbDeepscoreMatchingParametersScore":
                        self.params["AsKcbDeepscoreMatchingParameters"][
                            "score_cutoff"
                        ] = float(val)
                    case "AsKcbDeepscoreMatchingParametersDiff":
                        self.params["AsKcbDeepscoreMatchingParameters"][
                            "max_precursor_mass_diff"
                        ] = int(float(val))
                    case "MS2QueryResultsParametersCutoff":
                        self.params["MS2QueryResultsParameters"]["score_cutoff"] = (
                            float(val)
                        )
                    case _:
                        pass
        except Exception as e:
            msg = f"An error occurred during parameter assignment: {e!s}"
            raise RuntimeError(msg) from e

    def valid_antismash_id(self):
        """Validate antiSMASH job on antiSMASH website

        Raises:
            ValueError: antiSMASH JobID not found
            RuntimeError: timeout of connection
        """
        as_id = self.params["AsResultsParameters"].get("job_id")
        if not as_id:
            return

        try:
            url = f"https://antismash.secondarymetabolites.org/upload/{as_id}/"
            response = requests.get(url, timeout=5)
            zips = [
                line.split('"')[1]
                for line in response.text.splitlines()
                if ".zip" in line
            ]

            if not zips:
                raise ValueError("antiSMASH JobID not found on antiSMASH server.")
            else:
                for zip_file in zips:
                    save_path = self.uploads / self.uuid / zip_file.split(".")[0]
                    self.params["AsResultsParameters"]["directory_path"] = str(
                        save_path
                    )

        except Timeout as e:
            raise RuntimeError(
                f"Connection to antiSMASH server timed out: {e!s}"
            ) from e

    def valid_params(self):
        """Validate submitted files and parameters with fermo_core

        AsResultsParameters separate: job not downloaded yet

        Raises:
            ValueError: number of features too high
        """
        PeaktableParameters(**self.params.get("PeaktableParameters"))

        if current_app.config.get("ONLINE"):
            df = pd.read_csv(
                self.params.get("PeaktableParameters").get("filepath"), sep=","
            )
            if len(df) > current_app.config.get("MAXFEATURENR"):
                raise ValueError(
                    f"Too many features in peaktable (max: {self.max_features}). "
                    f"Please reduce or run FERMO in offline mode."
                )

        map_files = {
            "MsmsParameters": MsmsParameters,
            "GroupMetadataParameters": GroupMetadataParameters,
            "SpecLibParameters": SpecLibParameters,
            "PhenotypeParameters": PhenotypeParameters,
            "MS2QueryResultsParameters": MS2QueryResultsParameters,
        }

        for key, val in map_files.items():
            if self.params.get(key, {}).get("filepath") or self.params.get(key, {}).get(
                "dipath"
            ):
                val(**self.params.get(key))

        as_id = self.params["AsResultsParameters"].get("job_id")
        if as_id:
            ValidationManager().validate_float_zero_one(
                self.params["AsResultsParameters"].get("similarity_cutoff")
            )

        map_modules = {
            "AdductAnnotationParameters": AdductAnnotationParameters,
            "NeutralLossParameters": NeutralLossParameters,
            "FragmentAnnParameters": FragmentAnnParameters,
            "SpecSimNetworkCosineParameters": SpecSimNetworkCosineParameters,
            "SpecSimNetworkDeepscoreParameters": SpecSimNetworkDeepscoreParameters,
            "FeatureFilteringParameters": FeatureFilteringParameters,
            "BlankAssignmentParameters": BlankAssignmentParameters,
            "GroupFactAssignmentParameters": GroupFactAssignmentParameters,
            "PhenoQualAssgnParameters": PhenoQualAssgnParams,
            "PhenoQuantConcAssgnParameters": PhenoQuantConcAssgnParams,
            "PhenoQuantPercentAssgnParameters": PhenoQuantPercentAssgnParams,
            "SpectralLibMatchingCosineParameters": SpectralLibMatchingCosineParameters,
            "SpectralLibMatchingDeepscoreParameters": SpectralLibMatchingDeepscoreParameters,
            "AsKcbCosineMatchingParameters": AsKcbCosineMatchingParams,
            "AsKcbDeepscoreMatchingParameters": AsKcbDeepscoreMatchingParams,
        }

        for key, val in map_modules.items():
            if self.params.get(key, {}).get("activate_module"):
                val(**self.params.get(key))

    def load_session_id(self) -> Response | str:
        """Load session present on server"""
        try:
            self.check_session_id(self.data.get("SessionId"))
            return redirect(
                url_for("routes.task_result", job_id=self.data.get("SessionId"))
            )
        except Exception as e:
            current_app.logger.error(e)
            flash(f"{e!s}")
            return self.return_error()

    def load_param_id(self) -> str:
        """Load parameters from a session file present on server"""
        try:
            self.check_session_id(self.data.get("ParameterId"))
            return render_template(
                template_name_or_list="forms.html",
                job_id=self.data.get("ParameterId"),
                online=current_app.config.get("ONLINE"),
                params=self.params,
                max_size=current_app.config.get("MAX_CONTENT_LENGTH") or 0,
            )
        except Exception as e:
            current_app.logger.error(e)
            flash(f"{e!s}")
            return self.return_error()

    def load_session_file(self, file: FileStorage) -> Response | str:
        """Store session file, redirect to dashboard"""
        self.create_unique_dir()
        save_path = self.uploads / self.uuid / "results" / "out.fermo.session.json"

        try:
            size = self.determine_file_size(file)
            self.valid_file_size(size, secure_filename(file.filename))
            file.save(save_path)
            self.check_session_id(self.uuid)
            return redirect(url_for("routes.task_result", job_id=self.uuid))
        except Exception as e:
            current_app.logger.error(e)
            flash(f"{e!s}")
            shutil.rmtree(self.uploads.joinpath(self.uuid))
            return self.return_error()

    def load_param_file(self, file: FileStorage) -> str:
        """Load parameters from an uploaded session file

        Arguments:
            file: the uploaded session file (Werkzeug file obj)

        """
        self.create_unique_dir()
        save_path = self.uploads / self.uuid / "results" / "out.fermo.session.json"

        try:
            size = self.determine_file_size(file)
            self.valid_file_size(size, secure_filename(file.filename))
            file.save(save_path)
            self.check_session_id(self.uuid)
            return render_template(
                template_name_or_list="forms.html",
                job_id=secure_filename(file.filename),
                online=current_app.config.get("ONLINE"),
                params=self.params,
                max_size=current_app.config.get("MAX_CONTENT_LENGTH") or 0,
            )
        except Exception as e:
            current_app.logger.error(e)
            flash(f"{e!s}")
            shutil.rmtree(self.uploads.joinpath(self.uuid))
            return self.return_error()

    def new_analysis(self, files: Any) -> Response | str:
        """Prepare input params, init new analysis

        Arguments:
            files: a dict of Werkzeug file objects
        """
        self.create_unique_dir()
        save_path = self.uploads / self.uuid

        try:
            self.save_files(files)
            self.parse_forms()
            self.valid_antismash_id()
            self.valid_params()

            ValidationManager().validate_file_vs_jsonschema(
                self.params, f"{self.uuid}.parameters.json"
            )
            with open(save_path.joinpath(f"{self.uuid}.parameters.json"), "w") as out:
                json.dump(self.params, out, indent=2)

            email = None
            if self.data.get("emailInput") and self.data.get("emailInput") != "":
                email = str(self.data.get("emailInput"))

        except Exception as e:
            current_app.logger.error(e)
            flash(f"{e!s}")
            shutil.rmtree(self.uploads.joinpath(self.uuid))
            return self.return_error()

        start_job.apply_async(kwargs={"job_id": self.uuid, "email": email})

        return redirect(url_for("routes.job_submitted", job_id=self.uuid))
