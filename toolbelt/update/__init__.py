import os

import typer
import yaml

from toolbelt.constants import MAIN_CONFIG_PATH
from toolbelt.k8s import get_apv
from toolbelt.planet import Planet

from .release_infos import update_latest, update_root_config

update_app = typer.Typer()


@update_app.command()
def release_infos(rc_number: int, deploy_number: int):
    """
    Run post deploy script
    """

    raw_apv = get_apv(MAIN_CONFIG_PATH)
    apv = Planet.apv_analyze(raw_apv)
    launcher = apv.extra["launcher"].split("/")[1]

    update_latest(apv.version, launcher)
    update_root_config(
        apv.raw, f"planetariumhq/ninechronicles-headless:v{rc_number}-{deploy_number}"
    )
