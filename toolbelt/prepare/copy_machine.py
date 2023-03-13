from typing import Any, Callable, Dict, Optional

from toolbelt.constants import LINUX, MAC, WIN
from toolbelt.planet import Apv
from toolbelt.types import Network


class CopyMachine:
    def __init__(self, base_dir: str) -> None:
        self.os_list = [WIN, MAC, LINUX]
        self.required_os_list = [WIN]

        self.base_dir = base_dir
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
        additional_job: Optional[Callable[[str], Any]] = None,
        dry_run: bool = False,
    ):
        self.download(commit)
        self.preprocessing(
            additional_job=additional_job, network=network, apv=apv
        )
        if not dry_run:
            self.upload(bucket_prefix, network, apv, commit)

    def download(self, commit: str):
        raise NotImplementedError

    def preprocessing(
        self,
        *,
        additional_job: Optional[Callable[[str], Any]],
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
