import base64

from tests.path import *
from tests.testdata import read_file_as_json
from toolbelt.client import NaverClient

RELEASE_CDN_ID = "23177390"


def test_purge_cdn(requests_mock, mocker):
    client = NaverClient("test access", "test secret")

    requests_mock.get(
        f"/cdn/v2/requestGlobalCdnPurge?cdnInstanceNo={RELEASE_CDN_ID}&isWholePurge=true&isWholeDomain=true&responseFormatType=JSON",
        json=read_file_as_json(PURGE_CDN_PATH),
    )

    response = client.purge_cdn()

    assert response["ok"]
