from typing import Any, Callable, Dict

from toolbelt.constants import LINUX, MAC, WIN
from toolbelt.planet import Apv
from toolbelt.types import Network


class CopyMachine:
    def __init__(self, base_dir: str) -> None:
        self.os_list = [WIN, MAC, LINUX]
        self.required_os_list = [WIN]
        self.signing_os_list = [WIN]

        self.base_dir = base_dir
        self.dir_map: Dict[str, dict] = {
            WIN: {},
            MAC: {},
            LINUX: {},
        }

    def download(self, commit: str):
        raise NotImplementedError

    def preprocessing(self, additional_job: Callable[[str], Any]):
        raise NotImplementedError

    def upload(
        self,
        s3_prefix: str,
        network: Network,
        apv: Apv,
        commit: str,
    ):
        raise NotImplementedError
