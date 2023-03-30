#!/bin/bash
set -ex

IFS=$'\n'
echo $COMMAND_LIST

pip3 freeze
. /toolbelt/.venv/bin/activate

planet key import --passphrase $KEY_PASSPHRASE $KEY_PRIVATE

for cmd in $COMMAND_LIST
do
  python3 /toolbelt/cli.py $cmd
done
