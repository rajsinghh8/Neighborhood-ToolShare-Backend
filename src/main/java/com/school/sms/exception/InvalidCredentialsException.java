package com.school.sms.exception;

/** Bad username/password, or an unknown/expired refresh token (HTTP 401). */
public class InvalidCredentialsException extends RuntimeException {

    public InvalidCredentialsException(String message) {
        super(message);
    }
}
