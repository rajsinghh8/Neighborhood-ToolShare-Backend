package com.school.sms.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/** Bound from {@code app.kafka.*}. */
@ConfigurationProperties(prefix = "app.kafka")
public record KafkaTopicProperties(
        String topic,
        int partitions,
        long relayIntervalMs,
        int relayBatchSize,
        long sendTimeoutMs,
        int maxConsumerAttempts) {

    /** Dead-letter topic that receives events the consumer repeatedly failed to process. */
    public String deadLetterTopic() {
        return topic + ".dlq";
    }
}
