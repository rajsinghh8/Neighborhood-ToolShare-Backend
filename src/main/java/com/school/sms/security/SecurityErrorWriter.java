package com.school.sms.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.school.sms.exception.ApiError;
import com.school.sms.web.CorrelationIdFilter;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;

/** Writes the uniform {@link ApiError} envelope for rejections raised inside the security filter chain. */
@Component
class SecurityErrorWriter {

    private static final Logger LOG = LoggerFactory.getLogger(SecurityErrorWriter.class);

    private final ObjectMapper objectMapper;

    SecurityErrorWriter(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    void write(HttpServletResponse response, HttpStatus status, String message) throws IOException {
        String correlationId = CorrelationIdFilter.currentCorrelationId();
        LOG.warn("Request rejected with {} [correlationId={}]", status.value(), correlationId);
        response.setStatus(status.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        ApiError body = ApiError.of(status.value(), status.getReasonPhrase(), message, correlationId);
        objectMapper.writeValue(response.getOutputStream(), body);
    }
}
