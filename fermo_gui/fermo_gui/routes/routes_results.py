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
from pathlib import Path
from typing import Union

from flask import Response, current_app, redirect, render_template, request, url_for

from fermo_gui.analysis.dashboard_manager import DashboardManager
from fermo_gui.analysis.general_manager import GeneralManager
from fermo_gui.routes import bp


@bp.route("/results/job_failed/<job_id>/")
def job_failed(job_id: str) -> Union[str, Response]:
    """Render the job_failed html.

    Assumes that every failed job should have a logfile; if not found, redirect to
    'job_not_found' page.

    Arguments:
        job_id: the job identifier, provided by the URL variable

    Returns:
        The job_failed page for the job ID or a redirect to 'job_not_found' page.
    """
    try:
        with open(
            Path(current_app.config.get("UPLOAD_FOLDER"))
            .joinpath(job_id)
            .joinpath("results")
            .joinpath("out.fermo.log"),
        ) as logfile:
            log = logfile.read().split("\n")
        return render_template("job_failed.html", data={"task_id": job_id, "log": log})
    except FileNotFoundError:
        return redirect(url_for("routes.job_not_found", job_id=job_id))


@bp.route("/results/job_not_found/<job_id>/")
def job_not_found(job_id: str) -> str:
    """Render the job_not_found page.

    Logical end-point of job routes.

    Arguments:
        job_id: the job identifier, provided by the URL variable

    Returns:
        The job_not_found page for the job ID
    """
    root_url = str(request.base_url.partition(f"/results/job_not_found/{job_id}/")[0])
    root_url = root_url.replace("http://thornton", "https://fermo", 1)
    job_data = {
        "task_id": job_id,
        "root_url": root_url,
    }
    return render_template("job_not_found.html", job_data=job_data)


@bp.route("/results/<job_id>/", methods=["GET", "POST"])
def task_result(job_id: str) -> Union[str, Response]:
    """Render the result dashboard page for the given job id if found.

    Arguments:
        job_id: the job identifier, provided by the URL variable

    Returns:
        The dashboard page or the job_not_found page
    """
    try:
        sess_path = Path(current_app.config.get("UPLOAD_FOLDER")).joinpath(
            f"{job_id}/results/out.fermo.session.json"
        )
        with open(sess_path) as infile:
            session = json.load(infile)
    except Exception as e:
        current_app.logger.error(e)
        return redirect(url_for("routes.job_not_found", job_id=job_id))

    if request.method == "GET":
        manager = DashboardManager()
        manager.prepare_data_get(session)
        return render_template(
            "dashboard.html", data=manager.provide_data_get(), job_id=job_id
        )
