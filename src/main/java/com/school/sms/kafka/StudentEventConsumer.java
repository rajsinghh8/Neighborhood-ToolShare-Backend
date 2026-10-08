package com.school.sms.kafka;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;

/**
 * Consumes student events. The offset is committed only after the event was processed durably;
 * any exception propagates to the container's error handler (bounded retries, then dead-letter).
 */
@Component
public class StudentEventConsumer {

    private final ObjectMapper objectMapper;
    private final StudentEventProcessor processor;

    public StudentEventConsumer(ObjectMapper objectMapper, StudentEventProcessor processor) {
        this.objectMapper = objectMapper;
        this.processor = processor;
    }

    @KafkaListener(topics = "${app.kafka.topic}", groupId = "${spring.kafka.consumer.group-id}")
    public void onMessage(ConsumerRecord<String, String> record, Acknowledgment ack) {
        StudentEvent event = parse(record);
        processor.process(event, record);
        ack.acknowledge();
    }

    private StudentEvent parse(ConsumerRecord<String, String> record) {
        try {
            return objectMapper.readValue(record.value(), StudentEvent.class);
        } catch (JsonProcessingException e) {
            throw new EventDeserializationException(
                    "Invalid student event [key=" + record.key() + ", partition=" + record.partition()
                            + ", offset=" + record.offset() + "]", e);
        }
    }
}
