from typing import List, Optional, Tuple
from time import time
from toolbelt.github import get_latest_commit_hash
from toolbelt.client import GithubClient
from toolbelt.config import config
from toolbelt.github.constants import (
    GITHUB_ORG,
    HEADLESS_REPO,
    DP_REPO,
    SEED_REPO,
    WORLD_BOSS_REPO,
    INFRA_REPO,
)
from toolbelt.dockerhub.image import check_image_exists
import yaml
from toolbelt.dockerhub.constants import DOCKERHUB_ORG


ImageMetadata = Tuple[str, str, str]

COMMIT_BASE_TAG_PREFIX = "git-"


def update_images_of_values_file(
    file_path_at_github: str, image_sources: List[str]
):
    github_client = GithubClient(
        config.github_token, org=GITHUB_ORG, repo=HEADLESS_REPO
    )

    target_github_repo, file_path = file_path_at_github.split("/", 1)
    github_client.repo = target_github_repo
    head = github_client.get_ref(f"heads/main")
    new_branch = f"update-{file_path.split('/')[0]}-values-{int(time())}"
    github_client.create_ref(f"refs/heads/{new_branch}", head["object"]["sha"])
    main_branch_file_contents, response = github_client.get_content(
        file_path, "main"
    )

    if main_branch_file_contents is None:
        raise

    result_values_file = main_branch_file_contents

    for image_source in image_sources:
        docker_repo, ref_name, ref_value = extract_image_metadata(image_source)
        github_repo = dockerhub2github_repo(docker_repo)
        github_client.repo = github_repo

        if ref_name == "branch":
            commit_hash = get_latest_commit_hash(
                github_client, ref_name, ref_value
            )
            image_tag = build_commit_base_image_tag(commit_hash)
        elif ref_name == "commit":
            image_tag = build_commit_base_image_tag(ref_value)
        else:
            image_tag = ref_value
        image_is_exists = check_image_exists(docker_repo, image_tag)

        if not image_is_exists:
            raise

        result_values_file = update_image_tag(
            result_values_file,
            repo_to_change=docker_repo,
            tag_to_change=image_tag,
        )

    github_client.repo = target_github_repo
    github_client.update_content(
        commit=response["sha"],
        path=file_path,
        branch=new_branch,
        content=result_values_file,
        message=f"Update {docker_repo} to {image_tag}",
    )
    github_client.create_pull(
        title=f"Update values.yaml [{new_branch}]",
        head=new_branch,
        base="main",
        body=f"Update values.yaml\nCMD: {image_sources}",
        draft=False,
    )


def extract_image_metadata(
    image_source: str, delimiter: str = "/"
) -> ImageMetadata:
    # Example input: ninechronicles-headless/from tag 1

    docker_repo, source = image_source.split(delimiter)
    _, ref_name, ref_value = source.split(" ")
    return docker_repo, ref_name, ref_value


def build_commit_base_image_tag(commit_hash: str):
    return f"{COMMIT_BASE_TAG_PREFIX}{commit_hash}"


def dockerhub2github_repo(dockerhub_repo: str):
    dockerhub2github_repo_map = {
        "ninechronicles-headless": HEADLESS_REPO,
        "ninechronicles-dataprovider": DP_REPO,
        "libplanet-seed": SEED_REPO,
        # "nine-chronicles-bridge-observer": BRIDGE_OBSERVER_REPO,
        "world-boss-service": WORLD_BOSS_REPO,
    }

    return dockerhub2github_repo_map[dockerhub_repo]


def update_image_tag(
    contents: str, *, repo_to_change: str, tag_to_change: str
):
    def update_tag_recursively(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if (
                    key == "repository"
                    and f"{DOCKERHUB_ORG}/{repo_to_change}" in value
                ):
                    data["tag"] = tag_to_change
                else:
                    update_tag_recursively(value)
        elif isinstance(data, list):
            for item in data:
                update_tag_recursively(item)

    doc = yaml.safe_load(contents)
    update_tag_recursively(doc)
    new_doc = yaml.safe_dump(doc, sort_keys=False)

    return new_doc
