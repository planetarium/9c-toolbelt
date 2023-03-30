#!/bin/bash
set -ex

IFS=$'\n'
COMMAND_LIST="update bump-apv 14 internal
update bump-apv 14 main"

for cmd in $COMMAND_LIST
do
  echo $cmd
done
