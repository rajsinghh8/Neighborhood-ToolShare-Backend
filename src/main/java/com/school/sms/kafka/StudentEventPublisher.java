package com.school.sms.kafka;

/**
 * Abstraction the business layer uses to announce student changes. Implementations must not
 * block on, or fail because of, the message broker.
 */
public interface StudentEventPublisher {

    /**
     * Records an event for asynchronous delivery. Must be called inside the transaction of the
     * write the event describes, so the event is stored if and only if that write commits.
     */
    void publish(StudentEventType type, Long studentId);
}
