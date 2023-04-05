from typing import Dict, Optional, Union

import structlog

from toolbelt.apps.k8s.apv import get_apv
from toolbelt.client import GithubClient, SlackClient
from toolbelt.config import config
from toolbelt.constants import INTERNAL_CONFIG_PATH, MAIN_CONFIG_PATH, RELEASE_BASE_URL
from toolbelt.github.constants import (
    DP_REPO,
    HEADLESS_REPO,
    LAUNCHER_REPO,
    PLAYER_REPO,
    SEED_REPO,
)
from toolbelt.github.repos import get_latest_commits
from toolbelt.tools.planet import Apv, Planet, generate_extra
from toolbelt.types import Network, RepoInfos
from toolbelt.utils.url import build_download_url

from .launcher_copy_machine import LauncherCopyMachine
from .player_copy_machine import PlayerCopyMachine

logger = structlog.get_logger(__name__)

PROJECT_NAME_MAP = {"9c-launcher": "launcher", "NineChronicles": "player"}
APV_PATH_MAP: Dict[Network, str] = {
    "internal": INTERNAL_CONFIG_PATH,
    "main": MAIN_CONFIG_PATH,
}


def prepare_release(
    network: Network,
    rc_number: int,
    deploy_number: int,
    *,
    launcher_commit: Optional[str],
    player_commit: Optional[str],
    slack_channel: Optional[str],
    dry_run: bool,
    signing: bool,
):
    planet = Planet(config.key_address, config.key_passphrase)
    slack = SlackClient(config.slack_token)
    github_client = GithubClient(config.github_token, org="planetarium", repo="")

    logger.info(
        f"Start prepare release",
        network=network,
        isTest=config.env == "test",
        dry_run=dry_run,
        launcher_commit=launcher_commit,
        player_commit=player_commit,
    )
    if slack_channel:
        slack.send_simple_msg(
            slack_channel,
            f"[CI] Start prepare {network} release",
        )

    if config.env == "test":
        rc_branch = f"test-rc-v{rc_number}-{deploy_number}"
    else:
        rc_branch = f"rc-v{rc_number}-{deploy_number}"

    repos = [
        (LAUNCHER_REPO, rc_branch),
        (PLAYER_REPO, rc_branch),
        (HEADLESS_REPO, rc_branch),
        (DP_REPO, rc_branch),
        (SEED_REPO, "main"),
    ]

    repo_infos: RepoInfos = get_latest_commits(
        github_client,
        network,
        rc_number,
        repos,
        launcher_commit=launcher_commit,
        player_commit=player_commit,
    )

    apv = create_apv(planet, rc_number, network, repo_infos)
    logger.info(f"Confirmed apv_version", version=apv.version, extra=apv.extra)

    bucket_prefix = ""
    if config.env == "test":
        bucket_prefix = "ci-test/"

    headless_image_tag = dp_image_tag = f"v{rc_number}-{deploy_number}"

    logger.info("Start player, launcher artifacts copy")
    for info in repo_infos:
        repo, _, commit = info

        if network == "internal":
            if repo == HEADLESS_REPO:
                headless_image_tag = f"git-{commit}"
            elif repo == DP_REPO:
                dp_image_tag = f"git-{commit}"

        if repo == PLAYER_REPO or repo == LAUNCHER_REPO:
            copy_machine: Union[PlayerCopyMachine, LauncherCopyMachine]
            if repo == PLAYER_REPO:
                copy_machine = PlayerCopyMachine()
            elif repo == LAUNCHER_REPO:
                copy_machine = LauncherCopyMachine()
            copy_machine.run(
                commit,
                bucket_prefix,
                network,
                apv,
                dry_run=dry_run,
                signing=signing,
            )
            logger.info(f"Finish copy", repo=repo)

            download_url = build_download_url(
                RELEASE_BASE_URL,
                network,
                apv.version,
                PROJECT_NAME_MAP[repo],
                commit,
                "Windows.zip",
            )
            if slack_channel:
                slack.send_simple_msg(
                    slack_channel,
                    f"[CI] Prepared binary - {download_url}",
                )

    if slack_channel:
        slack.send_msg(
            slack_channel,
            text=f"[CI] Finish prepare *{network}* release\n*APV*\n  {apv.raw}\n*Image*\n  planetariumhq/ninechronicles-headless:{headless_image_tag}\n  planetariumhq/ninechronicles-dataprovider:{dp_image_tag}",
        )


def create_apv(
    planet: Planet,
    rc_number: int,
    network: Network,
    repo_infos: RepoInfos,
) -> Apv:
    prev_apv = get_apv(APV_PATH_MAP[network])
    prev_apv_detail = planet.apv_analyze(prev_apv)

    apvIncreaseRequired = True
    if network == "main":
        apv_version = rc_number

        if rc_number == prev_apv_detail.version:
            apvIncreaseRequired = False
    else:
        apv_version = prev_apv_detail.version + 1

    commit_map = {}
    for info in repo_infos:
        repo, _, commit = info
        try:
            commit_map[PROJECT_NAME_MAP[repo]] = commit
        except KeyError:
            pass

    extra = generate_extra(commit_map, apvIncreaseRequired, prev_apv_detail.extra)
    apv = planet.apv_sign(
        apv_version,
        **extra,
    )

    return apv
