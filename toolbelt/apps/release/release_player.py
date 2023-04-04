from typing import Optional

import structlog

from toolbelt.client import SlackClient
from toolbelt.config import config
from toolbelt.constants import BINARY_FILENAME_MAP, RELEASE_BASE_URL
from toolbelt.types import Network, Platforms
from toolbelt.utils.url import build_download_url

from .player_copy_machine import PlayerCopyMachine

logger = structlog.get_logger(__name__)


def release(
    commit_hash: str,
    platform: Platforms,
    version: int,
    network: Network,
    signing: bool,
    slack_channel: Optional[str],
):
    copy_machine = PlayerCopyMachine()
    slack = SlackClient(config.slack_token)

    target_s3_dir = create_target_s3_dir(network, version)

    copy_machine.run(
        platform,
        commit_hash,
        target_s3_dir,
        dry_run=config.env == "test",
        signing=signing,
    )

    download_url = build_download_url(
        RELEASE_BASE_URL,
        network,
        version,
        "player",
        commit_hash,
        BINARY_FILENAME_MAP[platform],
    )

    if slack_channel:
        slack.send_simple_msg(
            slack_channel,
            f"[CI] Prepared player {platform} binary - {download_url}",
        )


def create_target_s3_dir(network: Network, version: int):
    return f"{network}/{version}"
