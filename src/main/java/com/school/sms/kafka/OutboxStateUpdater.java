package com.school.sms.kafka;

import java.time.Instant;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/**
 * Short, separate transactions for outbox bookkeeping, so the relay never holds a database
 * transaction open while it waits for the broker.
 */
@Component
public class OutboxStateUpdater {

    private final OutboxEventRepository outboxEventRepository;

    public OutboxStateUpdater(OutboxEventRepository outboxEventRepository) {
        this.outboxEventRepository = outboxEventRepository;
    }

    @Transactional
    public void markPublished(Long outboxId) {
        outboxEventRepository.findById(outboxId)
                .ifPresent(event -> event.markPublished(Instant.now()));
    }

    @Transactional
    public void recordFailedAttempt(Long outboxId) {
        outboxEventRepository.findById(outboxId).ifPresent(OutboxEvent::recordFailedAttempt);
    }
}
