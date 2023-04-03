import json
import time
from typing import Callable

import requests
import structlog
from botocore.exceptions import ClientError

from toolbelt.client.new_aws import (
    DOWNLOAD_DISTRIBUTION_ID,
    RELEASE_DISTRIBUTION_ID,
    CFClient,
    S3Client,
)
from toolbelt.constants import RELEASE_BASE_URL, RELEASE_BUCKET
from toolbelt.tools.planet import Apv
from toolbelt.types import Network

from .constants import APV_HISTORY_FILE_NAME

logger = structlog.get_logger(__name__)


class APVHistoryManager:
    def __init__(self) -> None:
        self.s3_client = S3Client(RELEASE_BUCKET)
        self.cf_client = CFClient()

    def append_apv(self, apv: Apv, network: Network):
        exists_history_contents = self.download_apv_history(network)
        logger.debug("Exists apv_history file downloaded", network=network)

        exists_history_contents[apv.version] = {
            "number": apv.version,
            "signer": apv.signer,
            "raw": apv.raw,
            "timestamp": apv.extra["timestamp"],
        }

        file_path = self._get_apv_history_path(network)
        self._upload_apv_history(file_path, exists_history_contents)

        logger.info("New apv_history file uploaded", path=file_path)

        def check(contents: dict):
            try:
                contents[str(apv.version)]
                return True
            except KeyError:
                return False

        self._create_invalidation_with_retry(file_path, check)

    def remove_apv(self, number: int, network: Network):
        exists_history_contents = self.download_apv_history(network)
        logger.debug("Exists apv_history file downloaded", network=network)

        exists_history_contents.pop(str(number))

        file_path = self._get_apv_history_path(network)
        self._upload_apv_history(file_path, exists_history_contents)

        logger.info("Apv removed", path=file_path)

        def check(contents: dict):
            try:
                contents[str(number)]
                return False
            except KeyError:
                return True

        self._create_invalidation_with_retry(file_path, check)

    def download_apv_history(self, network: Network):
        try:
            exists_history_contents = json.loads(
                self.s3_client.read_file(self._get_apv_history_path(network))
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                exists_history_contents = {}
            else:
                raise

        return exists_history_contents

    def _upload_apv_history(self, file_path: str, contents: str):
        self.s3_client.upload(json.dumps(contents), file_path)

    def _create_invalidation_with_retry(
        self, file_path: str, check: Callable[[dict], bool]
    ):
        for _ in range(10):
            self.cf_client.create_invalidation([file_path], RELEASE_DISTRIBUTION_ID)
            self.cf_client.create_invalidation([file_path], DOWNLOAD_DISTRIBUTION_ID)

            r = requests.get(f"{RELEASE_BASE_URL}/{file_path}")
            apv_history_contents = r.json()

            if check(apv_history_contents):
                logger.info("Invalidation created", path=file_path)
                break
            else:
                logger.info("Not applied, retry", path=file_path, count=_)
                time.sleep(60)

    def _get_apv_history_path(self, network: Network):
        file_path = f"{network}/{APV_HISTORY_FILE_NAME}"
        return file_path
