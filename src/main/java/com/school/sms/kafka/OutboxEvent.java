package com.school.sms.kafka;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.Objects;

/** A message waiting to be (or already) delivered to Kafka, written in the business transaction. */
@Entity
@Table(name = "OUTBOX_EVENT", indexes = @Index(name = "IDX_OUTBOX_PUBLISHED_AT", columnList = "PUBLISHED_AT"))
public class OutboxEvent {

    private static final int TOPIC_LENGTH = 100;
    private static final int KEY_LENGTH = 100;
    private static final int PAYLOAD_LENGTH = 4000;

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "TOPIC", nullable = false, length = TOPIC_LENGTH)
    private String topic;

    @Column(name = "MESSAGE_KEY", nullable = false, length = KEY_LENGTH)
    private String messageKey;

    @Column(name = "PAYLOAD", nullable = false, length = PAYLOAD_LENGTH)
    private String payload;

    @Column(name = "CREATED_AT", nullable = false)
    private Instant createdAt;

    @Column(name = "PUBLISHED_AT")
    private Instant publishedAt;

    @Column(name = "ATTEMPTS", nullable = false)
    private int attempts;

    protected OutboxEvent() {
        // required by JPA
    }

    public OutboxEvent(String topic, String messageKey, String payload, Instant createdAt) {
        this.topic = topic;
        this.messageKey = messageKey;
        this.payload = payload;
        this.createdAt = createdAt;
    }

    public void markPublished(Instant publishedAt) {
        this.publishedAt = publishedAt;
    }

    public void recordFailedAttempt() {
        this.attempts++;
    }

    public Long getId() {
        return id;
    }

    public String getTopic() {
        return topic;
    }

    public String getMessageKey() {
        return messageKey;
    }

    public String getPayload() {
        return payload;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public Instant getPublishedAt() {
        return publishedAt;
    }

    public int getAttempts() {
        return attempts;
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof OutboxEvent that)) {
            return false;
        }
        return id != null && Objects.equals(id, that.id);
    }

    @Override
    public int hashCode() {
        return OutboxEvent.class.hashCode();
    }
}
