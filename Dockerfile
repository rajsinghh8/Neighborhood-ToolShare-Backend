## ---- Build stage ----
FROM eclipse-temurin:21-jdk-jammy AS build
WORKDIR /build

COPY mvnw mvnw
COPY .mvn .mvn
COPY pom.xml pom.xml
RUN chmod +x mvnw && ./mvnw -q -N dependency:go-offline || true

COPY src src
RUN chmod +x mvnw && ./mvnw package -DskipTests -q

## ---- Runtime stage ----
FROM eclipse-temurin:21-jre-jammy AS runtime
WORKDIR /app

COPY --from=build /build/target/app.jar app.jar

ENV SERVER_PORT=21552
EXPOSE 21552

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
