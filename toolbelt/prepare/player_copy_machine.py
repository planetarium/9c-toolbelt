import os
import zipfile
from typing import Any, Callable, Optional

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

from .copy_machine import CopyMachine

logger = structlog.get_logger(__name__)


class PlayerCopyMachine(CopyMachine):
    def download(self, commit: str):
        """
        It downloads the artifacts from GitHub for the given commit

        :param commit: The commit hash of the player you want to download
        :type commit: str
        """

        logger.debug("Download artifact", app="player", input=commit)

        github_client = GithubClient(
            config.github_token, org=GITHUB_ORG, repo=PLAYER_REPO
        )

        urls = get_artifact_urls(
            github_client,
            commit,
        )
        logger.debug("Get artifact urls", app="player", urls=urls)

        for target_os in self.os_list:
            logger.info(
                "Start download artifact",
                app="player",
                os=target_os,
                url=urls[target_os],
            )

            try:
                downloaded_path = download_from_github(
                    github_client, urls[target_os], target_os, self.base_dir
                )
                self.dir_map[target_os] = {"downloaded": downloaded_path}

                logger.info(
                    "Finish download",
                    app="player",
                    os=target_os,
                    path=downloaded_path,
                )
            except Exception:
                if target_os in self.required_os_list:
                    raise
                logger.error(
                    "Download artifact error occurred",
                    os=target_os,
                    exc_info=True,
                )

    def preprocessing(
        self,
        *,
        additional_job: Optional[Callable[[str], Any]],
        network: Optional[Network] = None,
        apv: Optional[Apv] = None,
    ):
        """
        It downloads the binary, extracts it, and then runs the additional_job function on the binary

        :param additional_job: A function that will be called after the binary is extracted
        :type additional_job: Callable[[str], Any]
        """

        logger.debug("Preprocessing", app="player", dir_status=self.dir_map)

        for target_os in self.os_list:
            logger.debug("Start extract artifact", app="player", os=target_os)

            try:
                with zipfile.ZipFile(
                    self.dir_map[target_os]["downloaded"], mode="r"
                ) as archive:
                    extract_path = f"{os.path.join(self.base_dir, target_os)}"
                    archive.extractall(path=extract_path)

                logger.info(
                    "Finish extract artifact",
                    app="player",
                    os=target_os,
                    extract_path=extract_path,
                )

                binary_path = os.path.join(extract_path, BINARY_FILENAME_MAP[target_os])

                self.dir_map[target_os]["binary"] = binary_path

                os.remove(self.dir_map[target_os]["downloaded"])
                self.dir_map[target_os].pop("downloaded")

                if additional_job:
                    logger.debug(
                        "Start additional job",
                        app="player",
                        os=target_os,
                        binary_path=binary_path,
                    )
                    additional_job(binary_path)
                    logger.debug(
                        "Finish additional job",
                        app="player",
                        os=target_os,
                        binary_path=binary_path,
                    )
            except Exception:
                if target_os in self.required_os_list:
                    raise
                logger.error(
                    "Extract artifact error occurred",
                    os=target_os,
                    exc_info=True,
                )

    def upload(self, s3_prefix: str, network: Network, apv: Apv, commit: str):
        """
        It uploads the player binary to S3

        :param s3_prefix: The prefix of the S3 bucket
        :type s3_prefix: str
        :param network: The network that the player is being built for
        :type network: Network
        :param apv: Apv
        :type apv: Apv
        :param commit: The commit hash of the current build
        :type commit: str
        """

        logger.debug(
            "Upload",
            app="player",
        )

        release_bucket = S3File(RELEASE_BUCKET)

        for target_os in self.os_list:
            try:
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
            except Exception:
                if target_os in self.required_os_list:
                    raise
                logger.error(
                    "Upload artifact error occurred",
                    os=target_os,
                    exc_info=True,
                )


def download_from_github(github_client: GithubClient, url: str, filename: str, dir: str):
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
