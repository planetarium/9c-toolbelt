import shutil
import subprocess
from datetime import datetime
from typing import List, Tuple
from toolbelt.config import config

from toolbelt.exceptions import PlanetError


class Esigner:
    def sign(
        self,
        credential_id: str,
        username: str,
        password: str,
        input_file_path: str,
        output_dir_path: str,
        totp_secret: str,
    ):
        config.esigner_path
        key_id = self.key(self.address)
        raw_command = f"planet apv sign --passphrase {self.passphrase} {key_id} {version} "

        for k, v in kwargs.items():
            raw_command += f"-e {k}={v} "

        out = subprocess.run(
            raw_command, capture_output=True, text=True, shell=True
        )
        if not out.stdout:
            raise PlanetError(
                "planet apv sign {{key_id}} {version}", out.stderr
            )

        return self.apv_analyze(out.stdout.strip())
