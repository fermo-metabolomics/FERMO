"""Class to manage data input forms for fermo session loading

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

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import StringField, SubmitField
from wtforms.validators import Optional


class SessionLoadForm(FlaskForm):
    """Handles the session loading fields."""

    session_file = FileField(
        label="FERMO Session File",
        description="Upload a previously created FERMO session file.",
        validators=[Optional(), FileAllowed(["json"])],
    )

    reload_existing_jobid = StringField(
        label="FERMO JobID",
        description=("Reload an existing FERMO job."),
        validators=[Optional()],
        render_kw={"placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"},
        # render_kw={"placeholder": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"},
    )

    load_session = SubmitField("Load Session")
