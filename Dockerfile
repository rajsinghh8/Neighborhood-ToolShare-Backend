# syntax=docker/dockerfile:1

# ---- Stage 1: build the executable jar -------------------------------------
FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /build

# Resolve dependencies first so this layer is cached until pom.xml changes.
COPY pom.xml .
RUN mvn -q -B dependency:go-offline

COPY src ./src
RUN mvn -q -B -DskipTests package

# ---- Stage 2: minimal runtime image -----------------------------------------
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app

RUN addgroup -S sms && adduser -S sms -G sms
COPY --from=build /build/target/app.jar app.jar
USER sms

ENV SERVER_PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=90s --retries=10 \
    CMD wget -qO- http://localhost:8000/health || exit 1

ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "/app/app.jar"]
