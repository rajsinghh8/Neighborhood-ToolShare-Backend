package com.school.sms.kafka;

import com.school.sms.config.KafkaTopicProperties;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import org.apache.kafka.common.KafkaException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.PageRequest;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * The single background publisher: forwards unpublished outbox rows to Kafka in id order using the
 * one shared producer. A row is marked published only after the broker confirmed the send. On any
 * failure the rest of the batch is skipped (to preserve ordering) and retried on the next tick, so
 * events are never dropped. {@code fixedDelay} guarantees ticks never overlap.
 */
@Component
public class OutboxRelay {

    private static final Logger log = LoggerFactory.getLogger(OutboxRelay.class);

    private final OutboxEventRepository outboxEventRepository;
    private final OutboxStateUpdater stateUpdater;
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final KafkaTopicProperties properties;

    public OutboxRelay(OutboxEventRepository outboxEventRepository,
                       OutboxStateUpdater stateUpdater,
                       KafkaTemplate<String, String> kafkaTemplate,
                       KafkaTopicProperties properties) {
        this.outboxEventRepository = outboxEventRepository;
        this.stateUpdater = stateUpdater;
        this.kafkaTemplate = kafkaTemplate;
        this.properties = properties;
    }

    @Scheduled(fixedDelayString = "${app.kafka.relay-interval-ms}")
    public void relay() {
        List<OutboxEvent> batch = outboxEventRepository.findByPublishedAtIsNullOrderByIdAsc(
                PageRequest.ofSize(properties.relayBatchSize()));
        for (OutboxEvent event : batch) {
            if (!deliver(event)) {
                return;
            }
        }
    }

    private boolean deliver(OutboxEvent event) {
        try {
            kafkaTemplate.send(event.getTopic(), event.getMessageKey(), event.getPayload())
                    .get(properties.sendTimeoutMs(), TimeUnit.MILLISECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            handleFailure(event, e);
            return false;
        } catch (ExecutionException | TimeoutException | KafkaException e) {
            handleFailure(event, e);
            return false;
        }
        stateUpdater.markPublished(event.getId());
        log.debug("Outbox event delivered [outboxId={}, key={}, topic={}]",
                event.getId(), event.getMessageKey(), event.getTopic());
        return true;
    }

    private void handleFailure(OutboxEvent event, Exception cause) {
        log.warn("Outbox delivery failed, will retry on next tick [outboxId={}, key={}, topic={}, attempts={}]",
                event.getId(), event.getMessageKey(), event.getTopic(), event.getAttempts() + 1, cause);
        stateUpdater.recordFailedAttempt(event.getId());
    }
}
