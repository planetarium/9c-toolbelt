import typer

from toolbelt.apps.k8s import get_apv
from toolbelt.constants import MAIN_CONFIG_PATH
from toolbelt.tools.planet import Planet
from toolbelt.utils.typer import network_arg

from .release_infos import update_latest, update_root_config
from .apv import update_apv_history

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
        apv.raw,
        f"planetariumhq/ninechronicles-headless:v{rc_number}-{deploy_number}",
    )


@update_app.command()
def bump_apv(
    number: int,
    network: str = network_arg,
):
    """
    Run post deploy script
    """

    update_apv_history(number, network)  # type:ignore
