"""Routes for pages related to data input and processing.

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
    request,
    url_for,
)
from pydantic import BaseModel
from werkzeug.utils import secure_filename

from fermo_gui.routes import bp


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
            )
        else:
            return self.return_error()

    def load_session_file(self, file: Any) -> Response | str:
        """Store session file, redirect to dashboard"""
        self.create_unique_dir()
        save_path = self.uploads / self.uuid / "results" / "out.fermo.session.json"
        file.save(save_path)

        if self.check_session_id(self.uuid):
            return redirect(url_for("routes.task_result", job_id=self.uuid))
        else:
            os.rmdir(self.uploads.joinpath(self.uuid))
            return self.return_error()

    def load_param_file(self, file: Any) -> str:
        """Load parameters from an uploaded session file"""
        self.create_unique_dir()
        save_path = self.uploads / self.uuid / "results" / "out.fermo.session.json"
        file.save(save_path)

        if self.check_session_id(self.uuid):
            return render_template(
                template_name_or_list="forms.html",
                job_id=secure_filename(file.filename),
                online=current_app.config.get("ONLINE"),
                params=self.params,
            )
        else:
            os.rmdir(self.uploads.joinpath(self.uuid))
            return self.return_error()


@bp.route("/analysis/dispatch/", methods=["GET", "POST"])
def dispatch() -> str | Response:
    """Dispatches request for job start, job load, params loading"""

    with open(current_app.config["DEFAULTS"]) as infile:
        defaults = json.load(infile)

    if request.method == "POST":
        parser = InputParser(
            data=request.form.to_dict(flat=True),
            params=defaults,
            uploads=Path(current_app.config.get("UPLOAD_FOLDER")),
        )

        if parser.data.get("loadSessionId"):
            return parser.load_session_id()
        elif parser.data.get("loadSessionFile"):
            return parser.load_session_file(file=request.files.get("SessionFile"))
        elif parser.data.get("loadParameterId"):
            return parser.load_param_id()
        elif parser.data.get("loadParameterFile"):
            return parser.load_param_file(file=request.files.get("ParameterFile"))
        elif parser.data.get("submitNewAnalysis"):
            return parser.new_analysis(files=request.files)
        elif parser.data.get("generateParamsFile"):
            return parser.return_params()
        else:
            current_app.logger.error("Invalid dispatch route")
            flash("Unknown dispatch route: please contact the FERMO developers")

    return render_template(
        template_name_or_list="forms.html",
        job_id=None,
        online=current_app.config.get("ONLINE"),
        params=defaults,
    )
