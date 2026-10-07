#!/bin/sh
# Runs the app in the foreground (the Tornado event loop never returns).
set -e
exec python -m app.main
