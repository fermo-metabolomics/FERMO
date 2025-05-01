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

from fermo_gui.routes import bp


class InputParser(BaseModel):
    """Converts raw user input into parameters file

    Attributes:
        uuid: the job uuid
        data: the user-submitted data
        params: the default params, to be updated with new values from data
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
    def convert_session_current(session: dict) -> dict:
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

    def load_session_id(self) -> Response | str:
        """Load session present on server"""
        try:
            if self.uploads.joinpath(self.data.get("SessionId")).exists():
                return redirect(
                    url_for("routes.task_result", job_id=self.data.get("SessionId"))
                )
            else:
                raise FileNotFoundError(
                    f'Could not find session ID on server: {self.data.get("SessionId")}'
                )
        except Exception as e:
            current_app.logger.error(e)
            flash(f"{e!s}")
            return self.return_error()

    def load_session_file(self, file: Any) -> Response | str:
        """Store session file, redirect to dashboard"""
        try:
            if not file:
                raise FileNotFoundError(
                    "Did not find session file - were there issues during the upload?"
                )

            self.create_unique_dir()

            session = json.load(file)

            with open(self.sess_schema) as infile:
                schema = json.load(infile)

            jsonschema.validate(instance=session, schema=schema)

            session = self.convert_session_current(session)

            save_path = self.uploads / self.uuid / "results" / "out.fermo.session.json"

            with open(save_path, "w") as out:
                json.dump(session, out, indent=2)

            return redirect(url_for("routes.task_result", job_id=self.uuid))

        except jsonschema.exceptions.ValidationError as e:
            msg = f"Incorrect FERMO session file formatting: {str(e).splitlines()[0]}"
            current_app.logger.error(msg)
            flash(f"{msg!s}")
            return self.return_error()
        except Exception as e:
            current_app.logger.error(e)
            flash(f"{e!s}")
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
