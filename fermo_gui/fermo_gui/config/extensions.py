"""Instantiates Flask extensions in a central place for convenient retrieval.

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

from celery import Celery, Task
from flask import Flask
from flask_mail import Mail

mail = Mail()


def configure_celery(app: Flask) -> Flask:
    """Configure the celery task manager.

    Arguments:
        app: The Flask app instance

    Returns:
        The Flask app instance with added extension Celery
    """
    if app.config.get("ONLINE"):
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(
            CELERY={
                "broker_url": "redis://localhost",
                "result_backend": "redis://localhost",
                "task_ignore_result": True,
            },
        )

    app.config.from_prefixed_env()

    class FlaskTask(Task):
        """Configure Celery Task to work with app Factory."""

        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return app
