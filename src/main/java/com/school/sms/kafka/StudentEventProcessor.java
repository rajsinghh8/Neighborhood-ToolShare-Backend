package com.school.sms.kafka;

import java.time.Instant;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Idempotent handling of one student event: the same event id has its effect exactly once. */
@Service
public class StudentEventProcessor {

    private static final Logger log = LoggerFactory.getLogger(StudentEventProcessor.class);

    private final ProcessedEventRepository processedEventRepository;

    public StudentEventProcessor(ProcessedEventRepository processedEventRepository) {
        this.processedEventRepository = processedEventRepository;
    }

    @Transactional
    public void process(StudentEvent event, ConsumerRecord<String, String> record) {
        String eventId = event.eventId().toString();
        if (processedEventRepository.existsById(eventId)) {
            log.debug("Duplicate student event ignored [eventId={}, studentId={}, partition={}, offset={}]",
                    eventId, event.studentId(), record.partition(), record.offset());
            return;
        }
        log.info("Received student event [eventId={}, type={}, studentId={}, key={}, partition={}, offset={}]",
                eventId, event.type().wireValue(), event.studentId(), record.key(),
                record.partition(), record.offset());
        processedEventRepository.save(new ProcessedEvent(eventId, Instant.now()));
    }
}
