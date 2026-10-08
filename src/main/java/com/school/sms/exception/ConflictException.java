package com.school.sms.exception;

/** The request conflicts with existing state, e.g. a duplicate username (HTTP 409). */
public class ConflictException extends RuntimeException {

    public ConflictException(String message) {
        super(message);
    }

    public ConflictException(String message, Throwable cause) {
        super(message, cause);
    }
}
