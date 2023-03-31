from datetime import datetime
from typing import TypedDict

from toolbelt.config import config
from toolbelt.manager import RemoteConfigManager
from toolbelt.tools.planet import Apv, Planet
from toolbelt.types import Network


class ApvDetail(TypedDict):
    number: int
    signer: str
    raw: str
    timestamp: str


def update_apv_history(number: int, network: Network):
    planet = Planet(config.key_address, config.key_passphrase)
    remote_config_manager = RemoteConfigManager()

    apv = generate_apv(planet, number)
    detail = ApvDetail(
        number=number,
        signer=apv.signer,
        raw=apv.raw,
        timestamp=apv.extra["timestamp"],
    )

    exists_history_contents = remote_config_manager.download_apv_history(network)
    exists_history_contents[number] = detail

    remote_config_manager.upload_apv_history(network, exists_history_contents)


def generate_apv(planet: Planet, number: int) -> Apv:
    timestamp = datetime.utcnow().strftime("%Y-%m-%d")
    extra = {}
    extra["timestamp"] = timestamp

    apv = planet.apv_sign(
        number,
        **extra,
    )

    return apv
