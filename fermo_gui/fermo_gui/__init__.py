"""Application factory of fermo_gui Flask app.

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

import contextlib
import logging
import os
import sys
from importlib import metadata
from pathlib import Path

import coloredlogs
from flask import Flask
from flask_wtf.csrf import CSRFProtect

from fermo_gui.config.extensions import configure_celery, mail
from fermo_gui.routes import bp


def create_app() -> Flask:
    """Factory function for Flask app, automatically detected by Flask.

    Returns:
        An instance of the Flask object
    """
    app = Flask(__name__, instance_relative_config=True)
    app = configure_app(app)
    app.url_map.strict_slashes = False
    verify_defaults(app)

    register_context_processors(app)
    app.register_blueprint(bp)

    mail.init_app(app)
    app = configure_celery(app)

    return app


def configure_app(app: Flask) -> Flask:
    """Configure the Flask app.

    Arguments:
        app: The Flask app instance
    """
    app = config_logger(app)

    app.config["SECRET_KEY"] = "dev"

    app.config["UPLOAD_FOLDER"] = Path(__file__).parent.joinpath("upload/")
    app.config["DEFAULTS"] = Path(__file__).parent.joinpath(
        "static/params/default_params.json"
    )
    app.config["ALLOWED_EXTENSIONS"] = {"json", "csv", "mgf", "session"}
    app.config["ONLINE"] = False
    app.config["ROOTURL"] = "fermo"
    app.config["MAX_RUN_TIME"] = None

    config_file = Path(__file__).parent.parent.joinpath("instance/config.py")
    if config_file.exists():
        app.config.from_pyfile(config_file)
        app.logger.info("Successfully loaded configuration from 'config.py'.")
    else:
        app.logger.warning("No 'config.py' file found. Default to dev settings.")
        app.logger.critical("INSECURE DEV MODE: DO NOT DEPLOY TO PRODUCTION!")

    if app.config["ONLINE"]:
        app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
        app.config["MAXFEATURENR"] = 3000

    csrf = CSRFProtect()
    csrf.init_app(app)

    return app


def config_logger(app: Flask) -> Flask:
    """Set up a named logger with nice formatting and attach to app

    Args:
        app: The Flask app

    Returns:
        The Flask app with attached logger
    """
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)

    logger = logging.getLogger("fermo")
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(
        coloredlogs.ColoredFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )

    file_handler = logging.FileHandler(
        Path(__file__).parent.joinpath("app.log"),
        mode="w",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    return app


def verify_defaults(app: Flask) -> None:
    """Verifies that default params are available

    Arguments:
        app: The Flask app

    Raises:
        RuntimeError: Data not found or empty
    """
    if not app.config["DEFAULTS"].exists():
        message = f"Could not find file '{app.config['DEFAULTS'].resolve()}'."
        app.logger.critical(message)
        raise RuntimeError(message)


def register_context_processors(app: Flask):
    """Register context processors to get access to variables across all pages.

    Arguments:
        app: The Flask app instance
    """

    @app.context_processor
    def set_version() -> dict:
        return {"version": metadata.version("fermo_gui")}
