#!/bin/bash
set -ex

echo $COMMAND

if [[ $COMMAND = "prepare" ]]; then
  planet key import --passphrase $KEY_PASSPHRASE $KEY_PRIVATE

  python3 /root/cli.py check headless-image $network $rc_number $deploy_number
  python3 /root/cli.py prepare release $network $rc_number $deploy_number --launcher-commit "$launcher_commit" --player-commit "$player_commit" --slack-channel "$SLACK_CHANNEL"
elif [[ $COMMAND = "update" ]]; then
  python3 /root/cli.py update release-infos
fi
