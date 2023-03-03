from typing import List, Optional, Tuple

import structlog
from github import Github

from toolbelt.types import Network, RepoInfos
from toolbelt.utils.parse import latest_tag

VALID_REPOS = (
    "9c-launcher",
    "NineChronicles",
    "NineChronicles.Headless",
    "NineChronicles.DataProvider",
    "libplanet-seed",
)
ORG = "planetarium"

logger = structlog.get_logger(__name__)


def get_latest_commits(
    github_client: Github,
    network: Network,
    rc: int,
    repos: List[Tuple[str, str]],
    *,
    launcher_commit: Optional[str] = None,
    player_commit: Optional[str] = None,
):
    repo_infos: RepoInfos = []
    for repo, branch in repos:
        if repo not in VALID_REPOS:
            raise ValueError("Not in valid repos")
        ref = f"heads/{branch}"

        if network == "internal":
            r = github_client.get_organization(ORG).get_repo(repo).get_git_ref(ref)

            if launcher_commit and repo == "9c-launcher":
                commit = launcher_commit
            elif player_commit and repo == "NineChronicles":
                commit = player_commit
            else:
                commit = r.object.sha
            tag = None
        elif network == "main":
            tags = github_client.get_organization(ORG).get_repo(repo).get_tags()
            tag, commit = latest_tag(tags, rc, prefix=create_tag_prefix(network))
        repo_infos.append((repo, tag, commit))

        logger.info(f"Found latest commit", repo=repo, tag=tag, commit=commit)

    return repo_infos


def create_tag_prefix(network: Network) -> str:
    prefix = ""

    if network != "main":
        prefix += f"{network}-"

    return prefix
