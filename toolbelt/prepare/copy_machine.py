import os
import tempfile
from typing import Dict, Literal, Optional

import structlog
import shutil

from toolbelt.config import config
from toolbelt.constants import LINUX, MAC, WIN
from toolbelt.esigner import Esigner
from toolbelt.planet import Apv
from toolbelt.types import Network
from toolbelt.utils.zip import compress, extract

logger = structlog.get_logger(__name__)


class CopyMachine:
    def __init__(self, app: Literal["player", "launcher"]) -> None:
        self.os_list = (
            WIN,
            MAC,
            LINUX,
        )
        self.required_os_list = (WIN,)

        self.app = app
        self.dir_map: Dict[str, dict] = {
            WIN: {},
            MAC: {},
            LINUX: {},
        }

    def run(
        self,
        commit: str,
        bucket_prefix: str,
        network: Network,
        apv: Apv,
        *,
        dry_run: bool = False,
        signing: bool = False,
    ):
        self.base_dir = "./tmp"

        for target_os in self.os_list:
            try:
                with tempfile.TemporaryDirectory() as tmp_path:
                    self.base_dir = tmp_path

                    self.download(target_os, commit)
                    self.preprocessing(target_os, network=network, apv=apv)
                    if signing:
                        if target_os == WIN:
                            signing_for_windows(
                                Esigner(),
                                self.dir_map[WIN]["binary"],
                                self.base_dir,
                                self.app,
                            )
                            logger.info(
                                "Finish signing", os=target_os, app=self.app
                            )
                    if not dry_run:
                        self.upload(
                            target_os,
                            commit=commit,
                            s3_prefix=bucket_prefix,
                            network=network,
                            apv=apv,
                        )
                    shutil.rmtree(self.base_dir)
            except Exception:
                if target_os in self.required_os_list:
                    raise
                logger.error(
                    "Download artifact error occurred",
                    os=target_os,
                    exc_info=True,
                )

    def download(self, target_os: str, commit: str):
        raise NotImplementedError

    def preprocessing(
        self,
        target_os: str,
        *,
        network: Optional[Network] = None,
        apv: Optional[Apv] = None,
    ):
        raise NotImplementedError

    def upload(
        self,
        target_os: str,
        *,
        commit: str,
        s3_prefix: str,
        network: Network,
        apv: Apv,
    ):
        raise NotImplementedError


def signing_for_windows(
    esigner: Esigner,
    binary_path: str,
    dir: str,
    target_app: Literal["player", "launcher"],
):
    check_storage(1)
    # 1. Extract binary
    extract_path = extract(dir, binary_path, use7z=False)
    check_storage(2)

    # 2. Move exe files
    input_dir = os.path.join(dir, "temp_input")
    os.mkdir(input_dir)
    if target_app == "player":
        os.rename(
            os.path.join(extract_path, "9c.exe"),
            os.path.join(input_dir, "9c.exe"),
        )
    elif target_app == "launcher":
        os.rename(
            os.path.join(extract_path, "Nine Chronicles.exe"),
            os.path.join(input_dir, "Nine Chronicles.exe"),
        )
    else:
        raise ValueError()

    # 3. signing
    output_dir = os.path.join(dir, "temp_output")
    os.mkdir(output_dir)
    # esigner.sign(
    #     **config.signing_secrets,
    #     input_dir_path=input_dir,
    #     output_dir_path=output_dir,
    # )
    if target_app == "player":
        os.rename(
            os.path.join(input_dir, "9c.exe"),
            os.path.join(output_dir, "9c.exe"),
        )
    elif target_app == "launcher":
        os.rename(
            os.path.join(input_dir, "Nine Chronicles.exe"),
            os.path.join(output_dir, "Nine Chronicles.exe"),
        )

    # 4. Re move exe files
    if target_app == "player":
        os.rename(
            os.path.join(output_dir, "9c.exe"),
            os.path.join(extract_path, "9c.exe"),
        )
    elif target_app == "launcher":
        os.rename(
            os.path.join(output_dir, "Nine Chronicles.exe"),
            os.path.join(extract_path, "Nine Chronicles.exe"),
        )

    # 5. Compress
    result_path = compress(dir, extract_path, binary_path, use7z=False)
    check_storage(3)

    return result_path


def check_storage(number):
    import subprocess

    print(
        f"{number}: ",
        subprocess.run(["df", "-h"], capture_output=True, text=True),
        "\n",
    )
