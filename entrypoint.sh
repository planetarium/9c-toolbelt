#!/bin/bash
set -ex

echo $COMMAND

pip3 freeze
. /toolbelt/.venv/bin/activate

if [[ $COMMAND = "prepare" ]]; then
  planet key import --passphrase $KEY_PASSPHRASE $KEY_PRIVATE

  python3 /toolbelt/cli.py check headless-image $NETWORK $RC_NUMBER $DEPLOY_NUMBER

  if [[ $SIGNING = "true" ]]; then
    python3 /toolbelt/cli.py prepare release $NETWORK $RC_NUMBER $DEPLOY_NUMBER --launcher-commit "$LAUNCHER_COMMIT" --player-commit "$PLAYER_COMMIT" --slack-channel "$SLACK_CHANNEL" --signing
  else
    python3 /toolbelt/cli.py prepare release $NETWORK $RC_NUMBER $DEPLOY_NUMBER --launcher-commit "$LAUNCHER_COMMIT" --player-commit "$PLAYER_COMMIT" --slack-channel "$SLACK_CHANNEL"
  fi
elif [[ $COMMAND = "update" ]]; then
  python3 /toolbelt/cli.py update release-infos $RC_NUMBER $DEPLOY_NUMBER
else
  python3 /toolbelt/cli.py --help
fi
