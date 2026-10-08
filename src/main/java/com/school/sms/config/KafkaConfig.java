package com.school.sms.config;

import org.apache.kafka.clients.admin.NewTopic;
import org.apache.kafka.common.TopicPartition;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.TopicBuilder;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.listener.DeadLetterPublishingRecoverer;
import org.springframework.kafka.listener.DefaultErrorHandler;
import org.springframework.util.backoff.FixedBackOff;

/**
 * Topic declarations and consumer error handling. The producer ({@link KafkaTemplate}) is the
 * single long-lived instance auto-configured by Spring Boot from {@code spring.kafka.*}.
 */
@Configuration
public class KafkaConfig {

    private static final int SINGLE_NODE_REPLICAS = 1;
    private static final int DEAD_LETTER_PARTITION = 0;
    private static final long RETRY_INTERVAL_MS = 1000L;

    @Bean
    public NewTopic studentEventsTopic(KafkaTopicProperties properties) {
        return TopicBuilder.name(properties.topic())
                .partitions(properties.partitions())
                .replicas(SINGLE_NODE_REPLICAS)
                .build();
    }

    @Bean
    public NewTopic studentEventsDeadLetterTopic(KafkaTopicProperties properties) {
        return TopicBuilder.name(properties.deadLetterTopic())
                .partitions(DEAD_LETTER_PARTITION + 1)
                .replicas(SINGLE_NODE_REPLICAS)
                .build();
    }

    /**
     * Retries a failing record a bounded number of times, then publishes it to the dead-letter
     * topic and commits its offset so a poison message never blocks the partition.
     */
    @Bean
    public DefaultErrorHandler kafkaErrorHandler(KafkaTemplate<String, String> kafkaTemplate,
                                                 KafkaTopicProperties properties) {
        DeadLetterPublishingRecoverer recoverer = new DeadLetterPublishingRecoverer(kafkaTemplate,
                (record, exception) -> new TopicPartition(properties.deadLetterTopic(), DEAD_LETTER_PARTITION));
        long retries = Math.max(0, properties.maxConsumerAttempts() - 1L);
        return new DefaultErrorHandler(recoverer, new FixedBackOff(RETRY_INTERVAL_MS, retries));
    }
}
