from typing import TypedDict

from toolbelt.client.github import GithubClient


class Artifacts(TypedDict):
    Windows: str
    OSX: str
    Linux: str


def get_artifact_urls(github_client: GithubClient, commit: str) -> Artifacts:
    workflow_runs = next(github_client.get_workflow_runs("success", head_sha=commit))

    artifacts_url = None
    for workflow in workflow_runs["workflow_runs"]:
        if workflow["name"] == "Build":
            artifacts_url = workflow["artifacts_url"]

    assert artifacts_url is not None

    artifacts_response = github_client._session.get(artifacts_url)
    artifacts = github_client.handle_response(artifacts_response)

    assert len(artifacts["artifacts"]) >= 3

    result: Artifacts = {
        "Windows": "",
        "OSX": "",
        "Linux": "",
    }

    for artifact in artifacts["artifacts"]:
        assert artifact["expired"] != True

        if "Windows" in artifact["name"]:
            result["Windows"] = artifact["archive_download_url"]
        if "OSX" in artifact["name"]:
            result["OSX"] = artifact["archive_download_url"]
        if "Linux" in artifact["name"]:
            result["Linux"] = artifact["archive_download_url"]

    assert result["Windows"] != ""

    return result
