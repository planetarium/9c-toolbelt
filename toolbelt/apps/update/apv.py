from typing import TypedDict
from toolbelt.types import Network
from toolbelt.tools.planet import Planet, Apv
from datetime import datetime
from toolbelt.config import config

from toolbelt.client.new_aws import S3Client
from toolbelt.constants import RELEASE_BUCKET
import json
from botocore.exceptions import ClientError

APV_HISTORY_FILE_NAME = "apv_history.json"


class ApvDetail(TypedDict):
    number: int
    signer: str
    raw: str
    timestamp: str


def update_apv_history(number: int, network: Network):
    planet = Planet(config.key_address, config.key_passphrase)
    s3_client = S3Client(RELEASE_BUCKET)

    apv = generate_apv(planet, number)
    detail = ApvDetail(
        number=number,
        signer=apv.signer,
        raw=apv.raw,
        timestamp=apv.extra["timestamp"],
    )

    file_path = f"{network}/{APV_HISTORY_FILE_NAME}"
    try:
        exists_history_contents = json.loads(s3_client.read_file(file_path))
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            exists_history_contents = {}
        else:
            raise
    exists_history_contents[str(number)] = detail

    s3_client.upload(json.dumps(exists_history_contents), file_path)


def generate_apv(planet: Planet, number: int) -> Apv:
    timestamp = datetime.utcnow().strftime("%Y-%m-%d")
    extra = {}
    extra["timestamp"] = timestamp

    apv = planet.apv_sign(
        number,
        **extra,
    )

    return apv
