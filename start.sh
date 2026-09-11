#!/usr/bin/env bash
set -e

SERVER_PORT="${SERVER_PORT:-21552}"

set -a
[ -f .env_3d186026-a490-405e-9a9b-e15f8ab6d64b ] && . ./.env_3d186026-a490-405e-9a9b-e15f8ab6d64b
set +a

if [ -x ./mvnw ]; then
    ./mvnw package -DskipTests -q
else
    mvn package -DskipTests -q
fi

java -jar target/app.jar --server.port="$SERVER_PORT"
