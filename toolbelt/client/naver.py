import hashlib
import hmac
import base64
import time

from toolbelt.client.session import BaseUrlSession
from toolbelt.exceptions import ResponseError

NAVER_CLOUD_BASE_URL = "https://ncloud.apigw.ntruss.com"
RELEASE_CDN_ID = "23177390"


class NaverClient:
    def __init__(self, access_key: str, secret_key: str) -> None:
        self._access_key = access_key
        self._secret_key = bytes(secret_key, 'UTF-8')
        self._session = BaseUrlSession(NAVER_CLOUD_BASE_URL)
        self._session.headers.update({"x-ncp-iam-access-key": self._access_key})

    def _make_signature(self, timestamp: str, method: str, uri: str) -> bytes:
        message = method + " " + uri + "\n" + timestamp + "\n" + self._access_key
        message = bytes(message, 'UTF-8')
        signing_key = base64.b64encode(hmac.new(self._secret_key, message, digestmod=hashlib.sha256).digest())
        return signing_key

    def purge_cdn(self):
        timestamp = int(time.time() * 1000)
        timestamp = str(timestamp)

        method = "GET"
        uri = f"/cdn/v2/requestGlobalCdnPurge?cdnInstanceNo={RELEASE_CDN_ID}&isWholePurge=true&isWholeDomain=true&responseFormatType=JSON"
        signature = self._make_signature(timestamp, method, uri)

        self._session.headers.update({
            "x-ncp-apigw-timestamp": timestamp,
            "x-ncp-apigw-signature-v2": signature
        })

        r = self._session.get(uri)
        r.raise_for_status()

        response = r.json()

        if not response["ok"]:
            raise ResponseError(f"NaverAPI ResponseError: body: {response}")

        return response