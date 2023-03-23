from toolbelt.github import get_latest_commit_hash_from_branch
from toolbelt.client import GithubClient
from tests.testdata import read_file_as_json
from tests.path import GET_REF_RESPONSE_PATH


def test_get_latest_commit_hash_from_branch(mocker):
    client = GithubClient("test", org="test", repo="test")
    response = read_file_as_json(GET_REF_RESPONSE_PATH)
    mocker.patch.object(
        client,
        "get_ref",
        return_value=response,
    )

    r = get_latest_commit_hash_from_branch(client, "test")
    assert r == response["object"]["sha"]
