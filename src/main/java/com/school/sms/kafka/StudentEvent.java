package com.school.sms.kafka;

import java.time.Instant;
import java.util.UUID;

/**
 * Event published to the student-events topic. {@code eventId} lets consumers de-duplicate
 * redeliveries; the Kafka message key is always the {@code studentId}.
 */
public record StudentEvent(UUID eventId, StudentEventType type, Long studentId, Instant timestamp) {

    public static StudentEvent of(StudentEventType type, Long studentId) {
        return new StudentEvent(UUID.randomUUID(), type, studentId, Instant.now());
    }
}
