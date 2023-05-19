from typing import Optional

import structlog
from toolbelt.client import slack

from toolbelt.manager.latest_metadata_manager import LatestMetadataManager

logger = structlog.get_logger(__name__)

def update(
        version: int,
        commit_hash: str,
        network: str,
        slack_channel: Optional[str] = None
):
    config_manager = LatestMetadataManager()
    config_manager.update_latest_version(version, commit_hash, network)

    #if slack_channel:
    #    slack.send_simple_msg(
    #        slack_channel,
    #        f"[CI] Prepared '{network}' player binary",
    #    )
