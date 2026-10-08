package com.school.sms.kafka;

/** A received Kafka message is not a valid student event; routed to retry and the dead-letter topic. */
public class EventDeserializationException extends RuntimeException {

    public EventDeserializationException(String message, Throwable cause) {
        super(message, cause);
    }
}
