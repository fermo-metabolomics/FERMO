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
from venv import logger

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
    def store_valid_file(file: FileStorage, save_path: Path) -> bool:
        """Check file size before dumping

        Args:
            file: a Werkzeug file object
            save_path: a Path to save the file to

        Returns:
            Bool indicating outcome for route handling
        """
        if current_app.config.get("ONLINE"):
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            if size > current_app.config.get("MAX_CONTENT_LENGTH"):
                e = (
                    f'File {file.filename} is bigger than the allowed '
                    f'{current_app.config.get("MAX_CONTENT_LENGTH")} bytes '
                    f'(found "{size}" bytes).'
                )
                current_app.logger.error(e)
                flash(e)
                return False

        file.save(save_path)
        return True

    def check_session_id(self, s_id: str) -> bool:
        """Check if job ID exists and sanitize the session file

        Also writes parameters from session file to self

        Args:
            s_id: a FERMO session UID

        Returns:
            A boolean

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
            current_app.logger.error(msg)
            flash(f"{msg!s}")
            return False
        except Exception as e:
            current_app.logger.error(e)
            flash(f"{e!s}")
            return False

        return True

    def load_session_id(self) -> Response | str:
        """Load session present on server"""
        if self.check_session_id(self.data.get("SessionId")):
            return redirect(
                url_for("routes.task_result", job_id=self.data.get("SessionId"))
            )
        else:
            return self.return_error()

    def load_param_id(self) -> str:
        """Load parameters from a session file present on server"""
        if self.check_session_id(self.data.get("ParameterId")):
            return render_template(
                template_name_or_list="forms.html",
                job_id=self.data.get("ParameterId"),
                online=current_app.config.get("ONLINE"),
                params=self.params,
                max_size=current_app.config.get("MAX_CONTENT_LENGTH") or 0,
            )
        else:
            return self.return_error()

    def load_session_file(self, file: FileStorage) -> Response | str:
        """Store session file, redirect to dashboard"""
        self.create_unique_dir()
        save_path = self.uploads / self.uuid / "results" / "out.fermo.session.json"

        if not self.store_valid_file(file, save_path):
            shutil.rmtree(self.uploads.joinpath(self.uuid))
            return self.return_error()

        if self.check_session_id(self.uuid):
            return redirect(url_for("routes.task_result", job_id=self.uuid))
        else:
            shutil.rmtree(self.uploads.joinpath(self.uuid))
            return self.return_error()

    def load_param_file(self, file: FileStorage) -> str:
        """Load parameters from an uploaded session file

        Arguments:
            file: the uploaded session file (Werkzeug file obj)

        """
        self.create_unique_dir()
        save_path = self.uploads / self.uuid / "results" / "out.fermo.session.json"

        if not self.store_valid_file(file, save_path):
            shutil.rmtree(self.uploads.joinpath(self.uuid))
            return self.return_error()

        if self.check_session_id(self.uuid):
            return render_template(
                template_name_or_list="forms.html",
                job_id=secure_filename(file.filename),
                online=current_app.config.get("ONLINE"),
                params=self.params,
                max_size=current_app.config.get("MAX_CONTENT_LENGTH") or 0,
            )
        else:
            shutil.rmtree(self.uploads.joinpath(self.uuid))
            return self.return_error()

    def new_analysis(self, files: Any) -> Response | str:
        """Prepare input params, init new analysis

        Arguments:
            files: a dict of Werkzeug file objects
        """

        def _check_content(f) -> int:
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            return size

        self.create_unique_dir()
        save_path = self.uploads / self.uuid
        mapping = {
            "PeaktableParametersFile": "PeaktableParameters",
            "MsmsParametersFile": "MsmsParameters",
            "PhenotypeParametersFile": "PhenotypeParameters",
            "GroupMetadataParametersFile": "GroupMetadataParameters",
            "MS2QueryResultsParametersFile": "MS2QueryResultsParameters",
        }
        for key, val in mapping.items():
            if key in files:
                file = files.get(key)

                if _check_content(file) == 0:
                    continue

                filepath = save_path / secure_filename(file.filename)
                self.params[val]["filepath"] = filepath.resolve()
                if not self.store_valid_file(file, filepath):
                    shutil.rmtree(save_path)
                    return self.return_error()

        speclibs = files.getlist("SpecLibParametersFiles")
        if any(secure_filename(f.filename) for f in speclibs):
            speclibpath = save_path / "spec_lib"
            speclibpath.mkdir()
            self.params["SpecLibParameters"]["dirpath"] = speclibpath.resolve()

            for file in speclibs:
                if _check_content(file) == 0:
                    continue

                filepath = speclibpath / secure_filename(file.filename)
                if not self.store_valid_file(file, filepath):
                    shutil.rmtree(save_path)
                    return self.return_error()

        # TODO: reorganize into two functions

        print(self.params)

        return self.return_error()

        # validate files and dump - separate function with a map for renaming and recognizing, check size
        # redo validation but take as much from input_processor as possible
        # redirect to job init
