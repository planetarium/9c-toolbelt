from toolbelt.client.github import GithubClient
from toolbelt.constants import LINUX, MAC, WIN


def get_artifact_urls(github_client: GithubClient, commit: str) -> dict:
    workflow_runs = next(github_client.get_workflow_runs("success", head_sha=commit))

    artifacts_url = None
    for workflow in workflow_runs["workflow_runs"]:
        if workflow["name"] == "Build":
            artifacts_url = workflow["artifacts_url"]

    assert artifacts_url is not None

    artifacts_response = github_client._session.get(artifacts_url)
    artifacts = github_client.handle_response(artifacts_response)

    assert len(artifacts["artifacts"]) >= 3

    result = {
        WIN: "",
        MAC: "",
        LINUX: "",
    }

    for artifact in artifacts["artifacts"]:
        assert artifact["expired"] != True

        if "Window" in artifact["name"]:
            result[WIN] = artifact["archive_download_url"]
        if "OSX" in artifact["name"]:
            result[MAC] = artifact["archive_download_url"]
        if "Linux" in artifact["name"]:
            result[LINUX] = artifact["archive_download_url"]

    assert result[WIN] != ""

    return result
