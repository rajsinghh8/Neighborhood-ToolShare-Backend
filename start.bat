@echo off
if not defined SERVER_PORT set SERVER_PORT=21552

for /f "usebackq tokens=1,* delims==" %%A in (.env_3d186026-a490-405e-9a9b-e15f8ab6d64b) do set %%A=%%B

if exist mvnw.cmd (
    call mvnw.cmd package -DskipTests -q
) else (
    call mvn package -DskipTests -q
)

java -jar target\app.jar --server.port=%SERVER_PORT%
