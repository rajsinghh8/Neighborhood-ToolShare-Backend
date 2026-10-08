package com.school.sms.kafka;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.Objects;

/** Marks an event id as handled by the consumer, so redeliveries have no further side effect. */
@Entity
@Table(name = "PROCESSED_EVENT")
public class ProcessedEvent {

    private static final int EVENT_ID_LENGTH = 36;

    @Id
    @Column(name = "EVENT_ID", nullable = false, length = EVENT_ID_LENGTH)
    private String eventId;

    @Column(name = "PROCESSED_AT", nullable = false)
    private Instant processedAt;

    protected ProcessedEvent() {
        // required by JPA
    }

    public ProcessedEvent(String eventId, Instant processedAt) {
        this.eventId = eventId;
        this.processedAt = processedAt;
    }

    public String getEventId() {
        return eventId;
    }

    public Instant getProcessedAt() {
        return processedAt;
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof ProcessedEvent that)) {
            return false;
        }
        return Objects.equals(eventId, that.eventId);
    }

    @Override
    public int hashCode() {
        return Objects.hashCode(eventId);
    }
}
