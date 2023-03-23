import json
import os

import pytest

from tests.constants import DATA_DIR


def get_slack_dir():
    return os.path.join("client", "slack")


FAILURE_RESPONSE_PATH = os.path.join(get_slack_dir(), "failureResponse.json")
POST_MESSAGE_RESPONSE_PATH = os.path.join(
    get_slack_dir(), "postMessageResponse.json"
)


def get_github_dir():
    return os.path.join("client", "github")


TAGS_RESPONSE_PATH = os.path.join(get_github_dir(), "tags.json")
PATH_CONTENT_RESPONSE_PATH = os.path.join(
    get_github_dir(), "path_content.json"
)
GET_REF_RESPONSE_PATH = os.path.join(get_github_dir(), "get_ref.json")
CREATE_PULL_RESPONSE_PATH = os.path.join(get_github_dir(), "create_pull.json")
WORKFLOW_RUNS_RESPONSE_PATH = os.path.join(
    get_github_dir(), "workflow_runs.json"
)
CREATE_REF_RESPONSE_PATH = os.path.join(get_github_dir(), "create_ref.json")
UPDATE_CONTENT_RESPONSE_PATH = os.path.join(
    get_github_dir(), "update_content.json"
)


def get_docker_dir():
    return os.path.join("client", "docker")


CHECK_IMAGE_EXISTS_RESPONSE_PATH = os.path.join(
    get_docker_dir(), "check_image_exists.json"
)
