# Checkpoint — job-c9459520-eefb-4d7d-b7c7-39536ee439ec

Project dir: /outputs/job-c9459520-eefb-4d7d-b7c7-39536ee439ec
Mode: greenfield Java monolith. Spring Boot 3.5.0, Java 21, Maven 3.9.9, Hibernate 6.6.2.Final (pinned via `hibernate.version`), Oracle (gvenzl/oracle-free:23-slim), Kafka (apache/kafka:4.3.1 KRaft), jjwt 0.12.6, springdoc 2.8.8.
Testing framework: curl. Linting: none. Base package `com.school.sms`. App port 8080 (compose also maps 8000:8080 for deploy contract). `/health` (actuator, base-path `/`) and `/docs` (+`/api-docs`) are public.
Host: Docker daemon was not running; started with `setsid dockerd`. No mvn on host -> use `maven:3.9.9-eclipse-temurin-21` via docker_exec.

## Packages / ownership
- Foundation (done by lead): pom.xml, application.yml, SmsApplication, config/{JwtProperties,AdminProperties,KafkaTopicProperties}, model/Role, dto/Dtos, exception/{NotFoundException,ConflictException,InvalidCredentialsException,ApiError,GlobalExceptionHandler}, web/CorrelationIdFilter (MDC key `correlationId`, `CorrelationIdFilter.currentCorrelationId()`), kafka/{StudentEvent,StudentEventType,StudentEventPublisher}
- Auth group: model/{AppUser,RefreshToken}, repository/{UserRepository,RefreshTokenRepository}, security/*, config/SecurityConfig, service/AuthService, controller/AuthController, seed/AdminSeeder
- Student group: model/Student, repository/StudentRepository, service/StudentService, controller/StudentController, common OffsetBasedPageRequest
- Kafka group: config/KafkaConfig, kafka/{StudentEventProducer (implements StudentEventPublisher -> outbox), OutboxEvent, OutboxEventRepository, OutboxRelay, StudentEventConsumer, ProcessedEvent(+repo), health indicator}
- Lead after groups: Dockerfile, docker-compose.yml, .env.example, README, curl test/report scripts.

## Contracts
- Error envelope ApiError(status,error,message,correlationId,timestamp). 401/403 from filter chain written by auth group's entry point / denied handler in same shape.
- Kafka topic `student-events` (DLQ `student-events.dlq`), key = studentId string, value = JSON of StudentEvent {eventId,type("created"|"updated"|"deleted"),studentId,timestamp}. Transactional outbox table OUTBOX_EVENT, idempotent consumer table PROCESSED_EVENT.
- Hard delete for students. Student delete emits "deleted".

## Status
- [x] STEP 1-3 foundation (pom, yml, DTOs, errors)
- [ ] Auth group
- [ ] Student group
- [ ] Kafka group
- [ ] Infra (Dockerfile/compose)
- [ ] Build check
- [ ] Boot verification + curl tests
- [ ] Reports (tests-artifacts/)
- [ ] Final Dockerfile run verification
