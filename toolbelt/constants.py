import os

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

# k8s config dir hard coding
INTERNAL_CONFIG_PATH = "internal/config.json"
ONBOARDING_CONFIG_PATH = "9c-launcher-config.json"
MAIN_CONFIG_PATH = "9c-launcher-config.json"

OUTPUT_DIR = os.path.abspath(os.path.join(ROOT_DIR, "output"))

RELEASE_BASE_URL = "https://release.nine-chronicles.com"
RELEASE_BUCKET = "9c-release.planetariumhq.com"

GITHUB_ORG = "planetarium"

K8S_REPO = "9c-k8s-config"
LAUNCHER_REPO = "9c-launcher"
PLAYER_REPO = "NineChronicles"
HEADLESS_REPO = "NineChronicles.Headless"
DP_REPO = "NineChronicles.DataProvider"
SEED_REPO = "libplanet-seed"

WIN = "Windows"
MAC = "macOS"
LINUX = "Linux"

BINARY_FILENAME_MAP = {
    WIN: "Windows.zip",
    MAC: "macOS.tar.gz",
    LINUX: "Linux.tar.gz",
}
