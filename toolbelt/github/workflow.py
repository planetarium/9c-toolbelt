from datetime import datetime
from datetime import timezone
from dateutil.parser import parse


from toolbelt.client.github import GithubClient
from toolbelt.constants import LINUX, MAC, WIN, BINARY_FILENAME_MAP


def get_artifact_urls(github_client: GithubClient, run_id) -> dict:
    artifacts_response = github_client.generate_artifacts_url(run_id)
    artifacts = github_client.handle_response(artifacts_response)

    result = {
        WIN: "",
        MAC: "",
        LINUX: "",
    }

    for artifact in artifacts["artifacts"]:
        assert not artifact["expired"]

        if "Window" in artifact["name"] or "win" in artifact["name"]:
            result[WIN] = artifact["archive_download_url"]
        if "OSX" in artifact["name"] or "mac" in artifact["name"]:
            result[MAC] = artifact["archive_download_url"]
        if "Linux" in artifact["name"] or "linux" in artifact["name"]:
            result[LINUX] = artifact["archive_download_url"]

    return result
