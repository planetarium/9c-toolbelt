import json
import os
import shutil
import tarfile
import zipfile
from typing import Any, Callable, Optional

import structlog
from py7zr import SevenZipFile

from toolbelt.client.aws import S3File
from toolbelt.constants import (
    BINARY_FILENAME_MAP,
    LINUX,
    MAC,
    RELEASE_BUCKET,
    WIN,
)
from toolbelt.planet.apv import Apv
from toolbelt.types import Network
from toolbelt.utils.url import build_s3_url

from .copy_machine import CopyMachine

ARTIFACT_BUCKET = "9c-artifacts"

logger = structlog.get_logger(__name__)


class LauncherCopyMachine(CopyMachine):
    def download(self, commit: str):
        logger.debug("Download artifact", app="launcher", input=commit)

        artifact_bucket = S3File(ARTIFACT_BUCKET)

        for target_os in self.os_list:
            try:
                file_name = BINARY_FILENAME_MAP[target_os]

                artifact_path = f"9c-launcher/{commit}/{file_name}"
                logger.debug(
                    "Download artifact info",
                    app="launcher",
                    os=target_os,
                    path=artifact_path,
                    file_name=file_name,
                )

                logger.info(
                    f"Start download launcher artifact", artifact=file_name
                )
                artifact_bucket.download(artifact_path, self.base_dir)
                self.dir_map[target_os] = {
                    "downloaded": os.path.join(self.base_dir, file_name)
                }
                logger.info(
                    f"Finish download launcher artifact",
                    artifact=file_name,
                    dst=self.dir_map[target_os]["downloaded"],
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
        logger.debug("Preprocessing", app="launcher")

        if not network or not apv:
            raise ValueError("Network and apv is required")

        release_bucket = S3File(RELEASE_BUCKET)

        for target_os in self.os_list:
            try:
                # 1. Extract launcher
                logger.debug("Extract launcher", app="launcher", os=target_os)

                extract_path = extract_launcher(
                    self.base_dir,
                    self.dir_map[target_os]["downloaded"],
                    target_os,
                )
                logger.debug(
                    "Finish extract launcher",
                    app="launcher",
                    os=target_os,
                    dst=extract_path,
                )

                # 2. Download config.json from release bucket and generate config
                logger.debug(
                    "Download config.json", app="launcher", os=target_os
                )

                downloaded_config_path = os.path.join(
                    self.base_dir, "config.json"
                )

                release_bucket.download(
                    f"{network}/config.json", self.base_dir
                )
                new_config = generate_config(
                    network, apv, downloaded_config_path
                )

                logger.info(
                    "Rewrite config.json", app="launcher", os=target_os
                )

                config_path = get_config_path(target_os)
                write_config(
                    os.path.join(self.base_dir, config_path), new_config
                )

                # 3. Compress launcher
                logger.debug(
                    "Start compress launcher",
                    app="launcher",
                    os=target_os,
                    target=extract_path,
                )
                binary_path = compress_launcher(
                    self.base_dir, extract_path, target_os
                )
                logger.info(
                    "Compress launcher",
                    app="launcher",
                    os=target_os,
                    result=binary_path,
                )

                # 4. clean
                self.dir_map[target_os]["binary"] = binary_path
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
                    "Download artifact error occurred",
                    os=target_os,
                    exc_info=True,
                )

    def upload(self, s3_prefix: str, network: Network, apv: Apv, commit: str):
        logger.debug(
            "Upload", app="launcher", input=[s3_prefix, network, apv, commit]
        )

        release_bucket = S3File(RELEASE_BUCKET)

        for target_os in self.os_list:
            try:
                release_path = s3_prefix + build_s3_url(
                    network,
                    apv.version,
                    "launcher",
                    commit,
                    BINARY_FILENAME_MAP[target_os],
                )
                logger.debug(
                    "Start Upload",
                    app="launcher",
                    path=release_path,
                )

                release_bucket.upload(
                    self.dir_map[target_os]["binary"],
                    release_path,
                )
                logger.info(
                    "Finish Upload",
                    app="launcher",
                    path=release_path,
                )

                release_bucket.upload(
                    os.path.join(self.base_dir, "config.json"),
                    f"{s3_prefix}{network}/config.json",
                )
                logger.debug(
                    "Finish Upload config.json",
                    app="launcher",
                    path=release_path,
                )
            except Exception:
                if target_os in self.required_os_list:
                    raise
                logger.error(
                    "Download artifact error occurred",
                    os=target_os,
                    exc_info=True,
                )


def get_config_path(os_name: str):
    if os_name in [WIN, LINUX]:
        return f"{os_name}/resources/app/config.json"
    elif os_name == MAC:
        return (
            f"{os_name}/Nine Chronicles.app/Contents/Resources/app/config.json"
        )
    else:
        raise ValueError(
            "Unsupported artifact name format: artifact name should be one of (macOS.tar.gz, Linux.tar.gz)"
        )


def write_config(config_path: str, config: str):
    with open(config_path, "w") as f:
        f.seek(0)
        json.dump(config, f, indent=4)
        f.truncate()


def extract_launcher(dir: str, binary_path: str, target_os: str) -> str:
    os_name, extension = BINARY_FILENAME_MAP[target_os].split(".", 1)
    dst_path = os.path.join(dir, os_name)

    if extension == "tar.gz":
        with tarfile.open(binary_path) as zip:
            zip.extractall(dst_path)
    else:
        with SevenZipFile(binary_path, mode="r") as archive:
            archive.extractall(dst_path)

    os.remove(binary_path)
    return dst_path


def compress_launcher(
    dir: str,
    target_dir: str,
    target_os: str,
) -> str:
    os_name, extension = BINARY_FILENAME_MAP[target_os].split(".", 1)
    dst_path = os.path.join(dir, f"{os_name}.{extension}")

    if extension == "tar.gz":
        with tarfile.open(dst_path, "w:gz") as zip:
            for arcname in os.listdir(target_dir):
                name = os.path.join(dir, os_name, arcname)
                zip.add(name, arcname=arcname)
    else:
        with zipfile.ZipFile(dst_path, mode="w") as archive:
            for p, _, files in os.walk(target_dir):
                for f in files:
                    filename = os.path.join(p, f)
                    archive.write(
                        filename=filename,
                        arcname=filename.removeprefix(target_dir),
                    )
    shutil.rmtree(target_dir)
    return dst_path


def generate_config(network: Network, apv: Apv, path: str) -> str:
    with open(path, mode="r+") as f:
        doc = json.load(f)
        doc["AppProtocolVersion"] = apv.raw
        if network != "main":
            doc[
                "BlockchainStoreDirName"
            ] = f"9c-{network}-rc-v{apv.version}-{apv.extra['timestamp']}"
        f.seek(0)
        json.dump(doc, f, indent=4)
        f.truncate()
    return doc
