import structlog

from toolbelt.client.github import GithubClient, WORKFLOW_STATUS
from toolbelt.constants import LINUX, MAC, WIN

logger = structlog.get_logger(__name__)

def get_artifact_urls(github_client: GithubClient, commit: str, run_id: Optional[str] = None) -> dict:
    for status in [
        "completed",
        "action_required",
        "cancelled",
        "failure",
        "neutral",
        "skipped",
        "stale",
        "success",
        "timed_out",
        "in_progress",
        "queued",
        "requested",
        "waiting",
        "pending",
    ]:
        workflow_runs = next(github_client.get_workflow_runs(status, head_sha=commit))

        artifacts_url = None
        for workflow in workflow_runs["workflow_runs"]:
            if workflow["name"] == "Build and Release":
                artifacts_url = workflow["artifacts_url"]

        logger.info(artifacts_url)
        if artifacts_url is not None:
            logger.info("Workflow Status", status=status)
            break
    if artifacts_url is None and run_id is not None:
        artifacts_url = github_client.generate_artifacts_url(run_id)

    assert artifacts_url is not None

    artifacts_response = github_client._session.get(artifacts_url)
    logger.info(artifacts_response)
    artifacts = github_client.handle_response(artifacts_response)

    result = {
        WIN: "",
        MAC: "",
        LINUX: "",
    }

    for artifact in artifacts["artifacts"]:
        assert artifact["expired"] != True

        if "Window" in artifact["name"] or "win" in artifact["name"]:
            result[WIN] = artifact["archive_download_url"]
        if "OSX" in artifact["name"] or "mac" in artifact["name"]:
            result[MAC] = artifact["archive_download_url"]
        if "Linux" in artifact["name"] or "linux" in artifact["name"]:
            result[LINUX] = artifact["archive_download_url"]

    return result
