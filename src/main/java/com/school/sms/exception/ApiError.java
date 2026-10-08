package com.school.sms.exception;

import java.time.Instant;

/** Uniform error envelope returned by every failing endpoint. */
public record ApiError(
        int status,
        String error,
        String message,
        String correlationId,
        Instant timestamp) {

    public static ApiError of(int status, String error, String message, String correlationId) {
        return new ApiError(status, error, message, correlationId, Instant.now());
    }
}
