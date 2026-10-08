package com.school.sms.kafka;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.school.sms.config.KafkaTopicProperties;
import java.time.Instant;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

/**
 * Stores student events in the transactional outbox. It never touches the broker: delivery is the
 * job of {@link OutboxRelay}, so API latency and availability are independent of Kafka.
 */
@Component
public class StudentEventProducer implements StudentEventPublisher {

    private static final Logger log = LoggerFactory.getLogger(StudentEventProducer.class);

    private final OutboxEventRepository outboxEventRepository;
    private final KafkaTopicProperties properties;
    private final ObjectMapper objectMapper;

    public StudentEventProducer(OutboxEventRepository outboxEventRepository,
                                KafkaTopicProperties properties,
                                ObjectMapper objectMapper) {
        this.outboxEventRepository = outboxEventRepository;
        this.properties = properties;
        this.objectMapper = objectMapper;
    }

    @Override
    @Transactional(propagation = Propagation.MANDATORY)
    public void publish(StudentEventType type, Long studentId) {
        StudentEvent event = StudentEvent.of(type, studentId);
        OutboxEvent outboxEvent = new OutboxEvent(
                properties.topic(), String.valueOf(studentId), serialize(event), Instant.now());
        outboxEventRepository.save(outboxEvent);
        log.debug("Student event queued in outbox [eventId={}, type={}, studentId={}]",
                event.eventId(), type.wireValue(), studentId);
    }

    private String serialize(StudentEvent event) {
        try {
            return objectMapper.writeValueAsString(event);
        } catch (JsonProcessingException e) {
            throw new EventSerializationException(
                    "Cannot serialise student event " + event.eventId(), e);
        }
    }
}
