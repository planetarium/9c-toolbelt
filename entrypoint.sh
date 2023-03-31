#!/bin/bash
set -ex

IFS_OLD=$IFS
IFS=$'\n'
echo $COMMAND_LIST

pip3 freeze
. /toolbelt/.venv/bin/activate

if [[ $KEY_PRIVATE ]]; then
  planet key import --passphrase $KEY_PASSPHRASE $KEY_PRIVATE
fi

for cmd in $COMMAND_LIST
do
  IFS=$IFS_OLD
  python3 /toolbelt/cli.py `echo "$cmd" | tr -d "'"`
  IFS=$'\n'
done
