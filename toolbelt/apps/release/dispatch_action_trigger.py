from typing import Optional

import structlog
from toolbelt.client import GithubClient
from toolbelt.config import config

logger = structlog.get_logger(__name__)

def dispatch_action_trigger(target_repository: str, event_type: str): 
    github = GithubClient(config.github_token)
    github.repository_dispatch(target_repository, event_type)