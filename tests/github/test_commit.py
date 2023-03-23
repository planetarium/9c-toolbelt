from toolbelt.github import get_latest_commit_hash_from_branch
from toolbelt.client import GithubClient


def test_get_latest_commit_hash_from_branch(mocker):
    client = GithubClient("test", org="test", repo="test")
    mocker.patch.object(client, "get_ref", return_value="test")

    r = get_latest_commit_hash_from_branch(client, "test")
    print(r)
    raise
