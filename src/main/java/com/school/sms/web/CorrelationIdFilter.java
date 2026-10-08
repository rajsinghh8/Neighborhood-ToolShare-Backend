package com.school.sms.web;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Optional;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * Establishes the correlation id for every request: reuses an incoming
 * {@code X-Correlation-ID}/{@code X-Request-ID} header or generates one, puts it in the
 * logging MDC and echoes it on the response. Runs before the Spring Security filter chain.
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class CorrelationIdFilter extends OncePerRequestFilter {

    public static final String CORRELATION_HEADER = "X-Correlation-ID";
    public static final String REQUEST_ID_HEADER = "X-Request-ID";
    public static final String MDC_KEY = "correlationId";

    /** Correlation id of the request being handled on this thread (empty outside a request). */
    public static String currentCorrelationId() {
        return Optional.ofNullable(MDC.get(MDC_KEY)).orElse("n/a");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        String correlationId = resolveCorrelationId(request);
        MDC.put(MDC_KEY, correlationId);
        response.setHeader(CORRELATION_HEADER, correlationId);
        try {
            chain.doFilter(request, response);
        } finally {
            MDC.remove(MDC_KEY);
        }
    }

    private String resolveCorrelationId(HttpServletRequest request) {
        return Optional.ofNullable(request.getHeader(CORRELATION_HEADER))
                .filter(value -> !value.isBlank())
                .or(() -> Optional.ofNullable(request.getHeader(REQUEST_ID_HEADER))
                        .filter(value -> !value.isBlank()))
                .orElseGet(() -> UUID.randomUUID().toString());
    }
}
