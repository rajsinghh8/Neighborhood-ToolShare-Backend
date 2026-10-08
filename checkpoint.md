# Checkpoint — job-c9459520-eefb-4d7d-b7c7-39536ee439ec

Project dir: /outputs/job-c9459520-eefb-4d7d-b7c7-39536ee439ec
Mode: greenfield Java monolith. Spring Boot 3.5.0, Java 21, Maven 3.9.9, Hibernate 6.6.2.Final (pinned via `hibernate.version`), Oracle (gvenzl/oracle-free:23-slim), Kafka (apache/kafka:4.3.1 KRaft), jjwt 0.12.6, springdoc 2.8.8.
Testing framework: curl. Linting: none. Base package `com.school.sms`. Container port 8000 (published 8000:8000; local default 8080). `/health` and `/docs` public.
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
- [x] Auth group (written, not compiled): model/{AppUser,RefreshToken}, repository/{User,RefreshToken}Repository, security/{JwtService,JwtAuthFilter,RestAuthenticationEntryPoint,RestAccessDeniedHandler,SecurityErrorWriter(pkg-private helper)}, config/{SecurityConfig,OpenApiConfig}, service/AuthService, controller/AuthController, seed/AdminSeeder. Notes: RefreshTokenRepository has no deleteByUser (unused; rotation uses delete(entity)); SecurityConfig exposes a repository-backed UserDetailsService bean only to suppress Boot's generated default user; refresh() uses noRollbackFor so expired-token deletion persists.
- [x] Student group (written, not compiled): model/{Student,StudentMapper}, repository/{StudentRepository,OffsetBasedPageRequest}, service/StudentService, controller/StudentController. Mapper lives in model pkg (uses Student's protected ctor).
- [x] Kafka group (written, not compiled): config/KafkaConfig (topics + DefaultErrorHandler->DLQ partition 0, FixedBackOff 1s x (maxAttempts-1)); kafka/{OutboxEvent, OutboxEventRepository, OutboxStateUpdater (short @Transactional markPublished/recordFailedAttempt), OutboxRelay (@Scheduled, send+get(timeout) then mark), StudentEventProducer (MANDATORY tx, EventSerializationException), ProcessedEvent(+Repository), StudentEventProcessor.process(event, record), StudentEventConsumer (EventDeserializationException on bad JSON), OutboxHealthIndicator ("outbox")}. StudentService must call publish() inside its @Transactional method.
- [ ] Infra (Dockerfile/compose)
- [ ] Build check
- [ ] Boot verification + curl tests
- [ ] Reports (tests-artifacts/)
- [ ] Final Dockerfile run verification

## Final status (all done)
- [x] Auth, Student, Kafka groups; infra (Dockerfile, compose, .env.example, README); build green (mvn package)
- [x] Boot verification (jar on compose network, Oracle + Kafka real): 47/47 checks PASS (HTTP + KAFKA delivery, consumer log, duplicate delivery, DLQ, broker-down 2xx<1s + outbox + recovery)
- [x] Reports: tests-artifacts/{api_test_report.xlsx,project_report.docx,test_results.json}
- [x] Dockerfile built+run verified (container port 8000, /health 200, /docs 200); infra torn down
- Note: this host's kernel.shmmax=2^64-1 breaks Oracle startup (EOVERFLOW even for `cat`; docker `sysctls` and bind-mounts over /proc are refused by runc).
- [x] Deploy-contract fix: compose `oracle` now builds docker/oracle/Dockerfile (gvenzl image + static busybox + entrypoint that, only if /proc/sys/kernel/shmmax is unreadable, bind-mounts sane values as root with cap SYS_ADMIN, then `su oracle`). Healthcheck runs healthcheck.sh via busybox su. Verified: `docker compose up -d --build --wait` exit 0, oracle/kafka/app all healthy, /health 200, admin login at /api/v1/auth/login returns token.
