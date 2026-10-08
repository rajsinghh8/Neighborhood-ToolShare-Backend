package com.school.sms.kafka;

/** An event could not be converted to its JSON wire format. */
public class EventSerializationException extends RuntimeException {

    public EventSerializationException(String message, Throwable cause) {
        super(message, cause);
    }
}
