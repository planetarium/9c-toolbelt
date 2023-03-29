from typing import List

import typer

from .apv import get_apv
from .update_values import ValuesFileUpdater

k8s_app = typer.Typer()


@k8s_app.command()
def update_values(
    file_path_at_github: str = typer.Argument(
        ..., help="e.g. 9c-infra/9c-main/chart/values.yaml"
    ),
    image_sources: List[str] = typer.Argument(
        ...,
        help="Just you send separated strings (e.g. 'ninechronicles-headless/from tag 1', 'ninechronicles-dataprovider/from branch main', 'world-boss-service/from branch development')",
    ),
):
    """
    Update images like headless, data-provider, seed...

    """

    ValuesFileUpdater().update(file_path_at_github, image_sources)


__all__ = ["update_values", "get_apv"]
