import os
from typing import Dict, Literal, Optional

from toolbelt.config import config
from toolbelt.constants import LINUX, MAC, WIN
from toolbelt.esigner import Esigner
from toolbelt.planet import Apv
from toolbelt.types import Network
from toolbelt.utils.zip import compress, extract


class CopyMachine:
    def __init__(
        self, base_dir: str, app: Literal["player", "launcher"]
    ) -> None:
        self.os_list = [WIN, MAC, LINUX]
        self.required_os_list = [WIN]

        self.base_dir = base_dir
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
        self.download(commit)
        self.preprocessing(network=network, apv=apv)
        if signing:
            signing_for_windows(
                Esigner(),
                self.dir_map[WIN]["binary"],
                self.base_dir,
                self.app,
            )
        if not dry_run:
            self.upload(bucket_prefix, network, apv, commit)

    def download(self, commit: str):
        raise NotImplementedError

    def preprocessing(
        self,
        *,
        network: Optional[Network] = None,
        apv: Optional[Apv] = None,
    ):
        raise NotImplementedError

    def upload(
        self,
        s3_prefix: str,
        network: Network,
        apv: Apv,
        commit: str,
    ):
        raise NotImplementedError


def signing_for_windows(
    esigner: Esigner,
    binary_path: str,
    dir: str,
    target_app: Literal["player", "launcher"],
):
    # 1. Extract binary
    extract_path = extract(dir, binary_path, use7z=False)

    # 2. Move exe files
    input_dir = os.path.join(dir, "temp_input")
    if target_app == "player":
        os.rename(
            os.path.join(extract_path, "Nine Chronicles.exe"),
            os.path.join(input_dir, "Nine Chronicles.exe"),
        )
    elif target_app == "launcher":
        os.rename(
            os.path.join(extract_path, "9c.exe"),
            os.path.join(input_dir, "9c.exe"),
        )
    else:
        raise ValueError()

    # 3. signing
    output_dir = os.path.join(dir, "temp_output")
    esigner.sign(
        **config.signing_secrets,
        input_dir_path=input_dir,
        output_dir_path=output_dir,
    )

    # 4. Re move exe files
    if target_app == "player":
        os.rename(
            os.path.join(output_dir, "Nine Chronicles.exe"),
            os.path.join(extract_path, "Nine Chronicles.exe"),
        )
    elif target_app == "launcher":
        os.rename(
            os.path.join(output_dir, "9c.exe"),
            os.path.join(extract_path, "9c.exe"),
        )

    # 5. Compress
    result_path = compress(dir, extract_path, binary_path, use7z=False)

    return result_path
