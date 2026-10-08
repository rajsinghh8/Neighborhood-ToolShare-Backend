package com.school.sms.exception;

import com.school.sms.web.CorrelationIdFilter;
import jakarta.validation.ConstraintViolationException;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.servlet.resource.NoResourceFoundException;

/** Single place that translates exceptions into the uniform {@link ApiError} envelope. */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger LOG = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    private static final String INVALID_REQUEST_MESSAGE = "Malformed or unreadable request body";
    private static final String INTERNAL_ERROR_MESSAGE = "An unexpected error occurred";
    private static final String CONFLICT_MESSAGE = "The request conflicts with existing data";

    @ExceptionHandler(NotFoundException.class)
    public ResponseEntity<ApiError> handleNotFound(NotFoundException ex) {
        return clientError(HttpStatus.NOT_FOUND, ex.getMessage(), ex);
    }

    @ExceptionHandler(NoResourceFoundException.class)
    public ResponseEntity<ApiError> handleNoResource(NoResourceFoundException ex) {
        return clientError(HttpStatus.NOT_FOUND, "Resource not found", ex);
    }

    @ExceptionHandler(ConflictException.class)
    public ResponseEntity<ApiError> handleConflict(ConflictException ex) {
        return clientError(HttpStatus.CONFLICT, ex.getMessage(), ex);
    }

    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<ApiError> handleDataIntegrity(DataIntegrityViolationException ex) {
        return clientError(HttpStatus.CONFLICT, CONFLICT_MESSAGE, ex);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiError> handleBodyValidation(MethodArgumentNotValidException ex) {
        String details = ex.getBindingResult().getFieldErrors().stream()
                .map(error -> error.getField() + ": " + error.getDefaultMessage())
                .sorted()
                .collect(Collectors.joining("; "));
        return clientError(HttpStatus.BAD_REQUEST, "Validation failed: " + details, ex);
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ApiError> handleParameterValidation(ConstraintViolationException ex) {
        String details = ex.getConstraintViolations().stream()
                .map(violation -> violation.getPropertyPath() + ": " + violation.getMessage())
                .sorted()
                .collect(Collectors.joining("; "));
        return clientError(HttpStatus.BAD_REQUEST, "Validation failed: " + details, ex);
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiError> handleUnreadableBody(HttpMessageNotReadableException ex) {
        return clientError(HttpStatus.BAD_REQUEST, INVALID_REQUEST_MESSAGE, ex);
    }

    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ResponseEntity<ApiError> handleTypeMismatch(MethodArgumentTypeMismatchException ex) {
        return clientError(HttpStatus.BAD_REQUEST, "Invalid value for parameter '" + ex.getName() + "'", ex);
    }

    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ResponseEntity<ApiError> handleMissingParameter(MissingServletRequestParameterException ex) {
        return clientError(HttpStatus.BAD_REQUEST, "Missing parameter '" + ex.getParameterName() + "'", ex);
    }

    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    public ResponseEntity<ApiError> handleMethodNotSupported(HttpRequestMethodNotSupportedException ex) {
        return clientError(HttpStatus.METHOD_NOT_ALLOWED, "HTTP method not supported for this endpoint", ex);
    }

    @ExceptionHandler({InvalidCredentialsException.class, BadCredentialsException.class})
    public ResponseEntity<ApiError> handleBadCredentials(RuntimeException ex) {
        return clientError(HttpStatus.UNAUTHORIZED, "Invalid credentials", ex);
    }

    @ExceptionHandler(AuthenticationException.class)
    public ResponseEntity<ApiError> handleAuthentication(AuthenticationException ex) {
        return clientError(HttpStatus.UNAUTHORIZED, "Authentication required", ex);
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ApiError> handleAccessDenied(AccessDeniedException ex) {
        return clientError(HttpStatus.FORBIDDEN, "Access denied: insufficient permissions", ex);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiError> handleUnexpected(Exception ex) {
        String correlationId = CorrelationIdFilter.currentCorrelationId();
        LOG.error("Unhandled exception [correlationId={}]", correlationId, ex);
        return build(HttpStatus.INTERNAL_SERVER_ERROR, INTERNAL_ERROR_MESSAGE, correlationId);
    }

    private ResponseEntity<ApiError> clientError(HttpStatus status, String message, Exception cause) {
        String correlationId = CorrelationIdFilter.currentCorrelationId();
        LOG.warn("Request rejected with {} [correlationId={}]: {}", status.value(), correlationId,
                cause.getClass().getSimpleName());
        LOG.debug("Rejection details [correlationId={}]", correlationId, cause);
        return build(status, message, correlationId);
    }

    private ResponseEntity<ApiError> build(HttpStatus status, String message, String correlationId) {
        ApiError body = ApiError.of(status.value(), status.getReasonPhrase(), message, correlationId);
        return ResponseEntity.status(status).body(body);
    }
}
