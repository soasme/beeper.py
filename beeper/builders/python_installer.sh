#!/bin/bash
# This script installs the bundled wheel distribution of %(application)s into
# a provided path where it will end up in a new virtualenv.

set -e

HERE="$(cd "$(dirname .)"; pwd)"
DATA_DIR=$HERE/.beeper-data
PY="python"
VIRTUAL_ENV=$HERE/venv

# Ensure Python exists
command -v "$PY" &> /dev/null || error "Given python interpreter not found ($PY)"

echo 'Setting up virtualenv'
"$PY" "$DATA_DIR/virtualenv.py" "$VIRTUAL_ENV"

VIRTUAL_ENV="$(cd "$VIRTUAL_ENV"; pwd)"

INSTALL_ARGS=''
if [ -f "$DATA_DIR/requirements.txt" ]; then
  INSTALL_ARGS="$INSTALL_ARGS"\ -r\ "$DATA_DIR/requirements.txt"
fi

echo "Installing %(application)s"
"$VIRTUAL_ENV/bin/pip" install --pre --no-index \
    --find-links "$DATA_DIR" wheel $INSTALL_ARGS | grep -v '^$'

# Potential post installation
cd "$HERE"
. "$VIRTUAL_ENV/bin/activate"
%(postinstall_commands)s

rm -rf $DATA_DIR

echo "Done."
