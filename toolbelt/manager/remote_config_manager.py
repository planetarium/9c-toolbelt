import json

from botocore.exceptions import ClientError

from toolbelt.client.new_aws import S3Client
from toolbelt.constants import RELEASE_BUCKET
from toolbelt.types import Network

from .constants import APV_HISTORY_FILE_NAME


class RemoteConfigManager:
    def __init__(self) -> None:
        self.s3_client = S3Client(RELEASE_BUCKET)

    def download_apv_history(self, network: Network):
        try:
            exists_history_contents = json.loads(
                self.s3_client.read_file(self.get_apv_history_path(network))
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                exists_history_contents = {}
            else:
                raise

        return exists_history_contents

    def upload_apv_history(self, network: Network, contents: str):
        self.s3_client.upload(json.dumps(contents), self.get_apv_history_path(network))

    def get_apv_history_path(self, network: Network):
        file_path = f"{network}/{APV_HISTORY_FILE_NAME}"
        return file_path
