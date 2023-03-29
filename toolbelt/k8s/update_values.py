from time import time
from typing import List, Tuple

import structlog
import yaml

from toolbelt.client import GithubClient
from toolbelt.config import config
from toolbelt.dockerhub.constants import DOCKERHUB_ORG
from toolbelt.dockerhub.image import check_image_exists
from toolbelt.github import get_latest_commit_hash
from toolbelt.github.constants import (
    DP_REPO,
    GITHUB_ORG,
    HEADLESS_REPO,
    SEED_REPO,
    WORLD_BOSS_REPO,
)

ImageMetadata = Tuple[str, str, str]

COMMIT_BASE_TAG_PREFIX = "git-"
logger = structlog.get_logger(__name__)


class ValuesFileUpdater:
    def __init__(self) -> None:
        self.github_client = GithubClient(
            config.github_token, org=GITHUB_ORG, repo=HEADLESS_REPO
        )

    def update(self, file_path_at_github: str, image_sources: List[str]):
        target_github_repo, file_path = file_path_at_github.split("/", 1)
        new_branch = f"update-{file_path.split('/')[0]}-values-{int(time())}"

        remote_values_file_contents, contents_response = self._init_github_ref(
            target_github_repo=target_github_repo,
            branch=new_branch,
            file_path=file_path,
        )
        result_values_file = remote_values_file_contents

        for image_source in image_sources:
            docker_repo, ref_name, ref_value = extract_image_metadata(image_source)
            github_repo = dockerhub2github_repo(docker_repo)
            image_tag = self._get_image_tag(
                github_repo=github_repo,
                docker_repo=docker_repo,
                ref_name=ref_name,
                ref_value=ref_value,
            )
            logger.info("Docker image tag", tag=image_tag)

            result_values_file = update_image_tag(
                result_values_file,
                repo_to_change=docker_repo,
                tag_to_change=image_tag,
            )

        pr_body = f"Update {file_path}\n\n" + "\n".join(image_sources)
        self._create_pr(
            target_github_repo=target_github_repo,
            base_commit_hash=contents_response["sha"],
            file_path=file_path,
            branch=new_branch,
            result_values=result_values_file,
            commit_msg=f"Update {file_path}",
            pr_body=pr_body,
        )
        logger.info("PR Created")

    def _init_github_ref(self, *, target_github_repo: str, branch: str, file_path: str):
        self.github_client.repo = target_github_repo
        head = self.github_client.get_ref(f"heads/main")
        logger.debug("Prev main branch ref", head_sha=head["object"]["sha"])

        self.github_client.create_ref(f"refs/heads/{branch}", head["object"]["sha"])
        logger.debug("Branch created", branch=branch)

        main_branch_file_contents, response = self.github_client.get_content(
            file_path, "main"
        )
        logger.debug("Prev values.yaml contents", content=main_branch_file_contents)

        if main_branch_file_contents is None:
            raise

        return main_branch_file_contents, response

    def _create_pr(
        self,
        *,
        target_github_repo: str,
        base_commit_hash: str,
        file_path: str,
        branch: str,
        result_values: str,
        commit_msg: str,
        pr_body: str,
    ):
        self.github_client.repo = target_github_repo
        self.github_client.update_content(
            commit=base_commit_hash,
            path=file_path,
            branch=branch,
            content=result_values,
            message=commit_msg,
        )
        self.github_client.create_pull(
            title=f"Update values.yaml [{branch}]",
            head=branch,
            base="main",
            body=pr_body,
            draft=False,
        )

    def _get_image_tag(
        self,
        *,
        github_repo: str,
        docker_repo: str,
        ref_name: str,
        ref_value: str,
    ) -> str:
        self.github_client.repo = github_repo

        logger.debug(
            "Create image tag",
            github_repo=github_repo,
            ref_name=ref_name,
            ref_value=ref_value,
        )
        if ref_name == "branch":
            commit_hash = get_latest_commit_hash(self.github_client, ref_name, ref_value)
            image_tag = build_commit_base_image_tag(commit_hash)
        elif ref_name == "commit":
            image_tag = build_commit_base_image_tag(ref_value)
        else:
            image_tag = ref_value

        logger.debug(
            "Check image is exists",
            image_tag=image_tag,
            docker_repo=docker_repo,
        )
        image_is_exists = check_image_exists(docker_repo, image_tag)

        if not image_is_exists:
            raise

        return image_tag


def extract_image_metadata(image_source: str, delimiter: str = "/") -> ImageMetadata:
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


def update_image_tag(contents: str, *, repo_to_change: str, tag_to_change: str):
    def update_tag_recursively(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "repository" and f"{DOCKERHUB_ORG}/{repo_to_change}" in value:
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
