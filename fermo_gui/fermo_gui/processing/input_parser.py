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
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

import jsonschema
from flask import (
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from pydantic import BaseModel
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

# class InputValidator(BaseModel):


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

    def create_unique_dir(self):
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
    def valid_file_size(size: int, name: str):
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

    def check_session_id(self, s_id: str):
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
        save_path_speclib = self.uploads / self.uuid / "spec_lib"

        try:
            for f_id in files:
                if f_id == "SpecLibParametersFiles":
                    continue
                file = files.get(f_id)
                size = self.determine_file_size(file)
                if size == 0:
                    continue
                self.valid_file_size(size, secure_filename(file.filename))
                filepath = save_path.joinpath(secure_filename(file.filename))
                file.save(filepath)
                key = f_id.removesuffix("File")
                self.params[key]["filepath"] = filepath.resolve()

            speclibs = files.getlist("SpecLibParametersFiles")
            if any(secure_filename(f.filename) for f in speclibs):
                save_path_speclib.mkdir()
                self.params["SpecLibParameters"]["dirpath"] = (
                    save_path_speclib.resolve()
                )

                for file in speclibs:
                    size = self.determine_file_size(file)
                    if size == 0:
                        continue
                    self.valid_file_size(size, secure_filename(file.filename))
                    filepath = save_path_speclib.joinpath(
                        secure_filename(file.filename)
                    )
                    file.save(filepath)

        except Exception as e:
            current_app.logger.error(e)
            flash(f"{e!s}")
            shutil.rmtree(self.uploads.joinpath(self.uuid))
            return self.return_error()

        # TODO: parse the settings into params file, run validation, start job, redirect

        # # TODO: run validation functions on the params file, possibly fermo_core-like
        #
        # mapping = {
        #     "PeaktableParametersFile": "PeaktableParameters",
        #     "MsmsParametersFile": "MsmsParameters",
        #     "PhenotypeParametersFile": "PhenotypeParameters",
        #     "GroupMetadataParametersFile": "GroupMetadataParameters",
        #     "MS2QueryResultsParametersFile": "MS2QueryResultsParameters",
        # }
        # for key, val in mapping.items():
        #     if key in files:
        #         file = files.get(key)
        #
        #         if _check_content(file) == 0:
        #             continue
        #
        #         filepath = save_path / secure_filename(file.filename)
        #
        #         if not self.store_valid_file(file, filepath):
        #             shutil.rmtree(save_path)
        #             return self.return_error()
        #

        #
        # # TODO: reorganize into two functions
        # # implement input file validation (rework function
        #
        # print(self.params)

        return self.return_error()

        # validate files and dump - separate function with a map for renaming and recognizing, check size
        # redo validation but take as much from input_processor as possible
        # redirect to job init
