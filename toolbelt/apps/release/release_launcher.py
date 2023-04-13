from typing import Optional

import structlog

from toolbelt.client import SlackClient
from toolbelt.config import config
from toolbelt.constants import BINARY_FILENAME_MAP, RELEASE_BASE_URL
from toolbelt.types import Network, Platforms

from .launcher_copy_machine import LauncherCopyMachine

logger = structlog.get_logger(__name__)


def release(
    commit_hash: str,
    platform: Platforms,
    version: int,
    network: Network,
    signing: bool,
    slack_channel: Optional[str],
):
    logger.debug(
        "Release Start",
        commit_hash=commit_hash,
        platform=platform,
        version=version,
        network=network,
        signing=signing,
        slack_channel=slack_channel,
    )

    copy_machine = LauncherCopyMachine()
    slack = SlackClient(config.slack_token)

    target_s3_dir = create_target_s3_dir(network, version)
    logger.debug("Target s3 dir", dir=target_s3_dir)

    logger.debug("Start copy")
    copy_machine.run(
        platform,
        commit_hash,
        target_s3_dir,
        dry_run=config.env == "test",
        signing=signing,
    )

    download_url = f"{RELEASE_BASE_URL}/{target_s3_dir}/{BINARY_FILENAME_MAP[platform]}"

    if slack_channel:
        slack.send_simple_msg(
            slack_channel,
            f"[CI] Prepared launcher '{platform}' binary - {download_url}",
        )


def create_target_s3_dir(network: Network, version: int):
    return f"{network}/launcher/{version}"
