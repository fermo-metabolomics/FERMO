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
from pathlib import Path

from flask import (
    Response,
    current_app,
    flash,
    render_template,
    request,
)

from fermo_gui.processing.input_parser import InputParser
from fermo_gui.routes import bp


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
        else:
            current_app.logger.error("Invalid dispatch route")
            flash("Unknown dispatch route: please contact the FERMO developers")

    return render_template(
        template_name_or_list="forms.html",
        job_id=None,
        online=current_app.config.get("ONLINE"),
        params=defaults,
        max_size=current_app.config.get("MAX_CONTENT_LENGTH") or 0,
    )


@bp.route("/analysis/job_submitted/<job_id>/", methods=["GET"])
def job_submitted(job_id: str) -> str:
    """Placeholder during calculation."""
    online = current_app.config.get("ONLINE")
    return render_template("job_submitted.html", job_id=job_id, online=online)
