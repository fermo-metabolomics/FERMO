"""Routes and logic for results pages.

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
from typing import Union

from flask import Response, current_app, redirect, render_template, request, url_for

from fermo_gui.analysis.dashboard_manager import DashboardManager
from fermo_gui.routes import bp


@bp.route("/results/job_failed/<job_id>/")
def job_failed(job_id: str) -> str | Response:
    """Render the job_failed html."""
    job_path = current_app.config.get("UPLOAD_FOLDER") / job_id
    fail_path = job_path / "results" / "out.failed.txt"
    log_path = job_path / "results" / "out.fermo.log"

    if not fail_path.exists():
        return redirect(url_for("routes.job_not_found", job_id=job_id))

    try:
        with open(log_path) as f:
            log = f.read().split("\n")
    except FileNotFoundError:
        log = []

    return render_template("job_failed.html", job_id=job_id, log=log)


@bp.route("/results/job_running/<job_id>/")
def job_running(job_id: str) -> str | Response:
    """Render the job_running html."""
    job_path = current_app.config.get("UPLOAD_FOLDER") / job_id
    log_path = job_path / "results" / "out.fermo.log"

    if not log_path.exists():
        return redirect(url_for("routes.job_not_found", job_id=job_id))

    try:
        with open(log_path) as f:
            log = f.read().split("\n")
    except FileNotFoundError:
        log = []

    return render_template("job_running.html", job_id=job_id, log=log)


@bp.route("/results/job_not_found/<job_id>/")
def job_not_found(job_id: str) -> str:
    """Logical end-point of job routes."""
    online = current_app.config.get("ONLINE")
    return render_template("job_not_found.html", job_id=job_id, online=online)


@bp.route("/results/<job_id>/", methods=["GET", "POST"])
def task_result(job_id: str) -> Union[str, Response]:
    """Render the result dashboard page for the given job id if found.

    Arguments:
        job_id: the job identifier, provided by the URL variable

    Returns:
        The dashboard page or the job_not_found page
    """
    job_path = current_app.config.get("UPLOAD_FOLDER") / job_id
    sess_path = job_path / "results" / "out.fermo.session.json"
    fail_path = job_path / "results" / "out.failed.txt"
    log_path = job_path / "results" / "out.fermo.log"

    if request.method == "GET":
        if sess_path.exists():
            with open(sess_path) as infile:
                session = json.load(infile)
            manager = DashboardManager()
            manager.prepare_data_get(session)
            return render_template(
                "dashboard.html", data=manager.provide_data_get(), job_id=job_id
            )
        elif fail_path.exists():
            return redirect(url_for("routes.job_failed", job_id=job_id))
        elif log_path.exists():
            return redirect(url_for("routes.job_running", job_id=job_id))
        else:
            return redirect(url_for("routes.job_not_found", job_id=job_id))
