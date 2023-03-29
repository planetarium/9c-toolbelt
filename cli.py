import typer

from toolbelt.check import check_app
from toolbelt.prepare import prepare_app
from toolbelt.update import update_app
from toolbelt.k8s import k8s_app

import structlog
import logging
from toolbelt.config import config

if config.env == "production":
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )

app = typer.Typer()
app.add_typer(check_app, name="check")
app.add_typer(prepare_app, name="prepare")
app.add_typer(update_app, name="update")
app.add_typer(k8s_app, name="k8s")

if __name__ == "__main__":
    app()
