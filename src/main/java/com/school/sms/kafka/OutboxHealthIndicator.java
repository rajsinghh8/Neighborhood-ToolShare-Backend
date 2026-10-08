package com.school.sms.kafka;

import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

/** Reports the number of events still waiting to be delivered to Kafka (component "outbox"). */
@Component("outboxHealthIndicator")
public class OutboxHealthIndicator implements HealthIndicator {

    private static final String BACKLOG_DETAIL = "outboxBacklog";

    private final OutboxEventRepository outboxEventRepository;

    public OutboxHealthIndicator(OutboxEventRepository outboxEventRepository) {
        this.outboxEventRepository = outboxEventRepository;
    }

    @Override
    public Health health() {
        try {
            return Health.up()
                    .withDetail(BACKLOG_DETAIL, outboxEventRepository.countByPublishedAtIsNull())
                    .build();
        } catch (RuntimeException e) {
            return Health.down(e).build();
        }
    }
}
