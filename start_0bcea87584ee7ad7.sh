#!/usr/bin/env bash
set -e
export SERVER_PORT="${SERVER_PORT:-25084}"
if [ -f "./start.sh" ]; then
  bash ./start.sh
else
  JAR=$(ls target/*.jar 2>/dev/null | head -1 || ls build/libs/*.jar 2>/dev/null | head -1)
  java -jar "$JAR" --server.port=$SERVER_PORT
fi
