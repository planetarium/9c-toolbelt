import os
from typing import Literal, Optional

import structlog

from toolbelt.client import GithubClient
from toolbelt.client.aws import S3File
from toolbelt.config import config
from toolbelt.constants import (
    BINARY_FILENAME_MAP,
    GITHUB_ORG,
    PLAYER_REPO,
    RELEASE_BUCKET,
)
from toolbelt.github.workflow import get_artifact_urls
from toolbelt.planet import Apv
from toolbelt.types import Network
from toolbelt.utils.url import build_s3_url
from toolbelt.utils.zip import extract as extract_player

from .copy_machine import CopyMachine

logger = structlog.get_logger(__name__)


class PlayerCopyMachine(CopyMachine):
    def __init__(
        self, base_dir: str, app: Literal["player", "launcher"]
    ) -> None:
        super().__init__(base_dir, app)

        self.urls: Optional[dict] = None

    def download(self, target_os: str, commit: str):
        logger.debug("Download artifact", app="player", input=commit)

        github_client = GithubClient(
            config.github_token, org=GITHUB_ORG, repo=PLAYER_REPO
        )

        if not self.urls:
            self.urls = get_artifact_urls(
                github_client,
                commit,
            )
            logger.debug("Get artifact urls", app="player", urls=self.urls)

        logger.info(
            "Start download artifact",
            app="player",
            os=target_os,
            url=self.urls[target_os],
        )

        downloaded_path = download_from_github(
            github_client, self.urls[target_os], target_os, self.base_dir
        )
        self.dir_map[target_os] = {"downloaded": downloaded_path}

        logger.info(
            "Finish download",
            app="player",
            os=target_os,
            path=downloaded_path,
        )

    def preprocessing(
        self,
        target_os: str,
        *,
        network: Optional[Network] = None,
        apv: Optional[Apv] = None,
    ):
        logger.debug("Preprocessing", app="player", dir_status=self.dir_map)

        logger.debug("Start extract artifact", app="player", os=target_os)

        extract_path = extract_player(
            self.base_dir, self.dir_map[target_os]["downloaded"], False
        )

        logger.info(
            "Finish extract artifact",
            app="player",
            os=target_os,
            extract_path=extract_path,
        )

        binary_path = os.path.join(
            extract_path, BINARY_FILENAME_MAP[target_os]
        )

        self.dir_map[target_os]["binary"] = binary_path
        self.dir_map[target_os].pop("downloaded")

    def upload(
        self,
        target_os: str,
        *,
        commit: str,
        s3_prefix: str,
        network: Network,
        apv: Apv,
    ):
        logger.debug(
            "Upload",
            app="player",
        )

        release_bucket = S3File(RELEASE_BUCKET)

        release_path = s3_prefix + build_s3_url(
            network,
            apv.version,
            "player",
            commit,
            BINARY_FILENAME_MAP[target_os],
        )
        logger.debug(
            "Release Path",
            app="player",
            os=target_os,
            path=release_path,
        )

        release_bucket.upload(
            self.dir_map[target_os]["binary"],
            release_path,
        )
        logger.info(
            "Upload Done",
            app="player",
            os=target_os,
            release_path=release_path,
        )
        os.remove(self.dir_map[target_os]["binary"])


def download_from_github(
    github_client: GithubClient, url: str, filename: str, dir: str
):
    """
    Download a file from a URL and save it to a file

    :param github_client: GithubClient
    :type github_client: GithubClient
    :param url: The URL of the zip file to download
    :type url: str
    :param filename: The name of the file you want to download
    :type filename: str
    :param dir: The directory to download the zip file to
    :type dir: str
    :return: A path to the downloaded file.
    """

    path = f"{os.path.join(dir, filename)}.zip"
    res = github_client._session.get(url)
    res.raise_for_status()

    with open(path, "wb") as f:
        for chunk in res.iter_content(chunk_size=1024):
            f.write(chunk)

    return path
