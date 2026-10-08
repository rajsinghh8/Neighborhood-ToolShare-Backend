package com.school.sms.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;
import java.util.Optional;
import org.springframework.http.HttpHeaders;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * Authenticates requests carrying a valid {@code Authorization: Bearer <jwt>} header. Requests
 * without a valid token continue unauthenticated; the entry point turns that into a 401.
 */
@Component
public class JwtAuthFilter extends OncePerRequestFilter {

    private static final String BEARER_PREFIX = "Bearer ";
    private static final String ROLE_AUTHORITY_PREFIX = "ROLE_";

    private final JwtService jwtService;

    public JwtAuthFilter(JwtService jwtService) {
        this.jwtService = jwtService;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        extractBearerToken(request)
                .filter(jwtService::isValid)
                .ifPresent(this::authenticate);
        chain.doFilter(request, response);
    }

    private Optional<String> extractBearerToken(HttpServletRequest request) {
        return Optional.ofNullable(request.getHeader(HttpHeaders.AUTHORIZATION))
                .filter(header -> header.startsWith(BEARER_PREFIX))
                .map(header -> header.substring(BEARER_PREFIX.length()).trim());
    }

    private void authenticate(String token) {
        var authority = new SimpleGrantedAuthority(ROLE_AUTHORITY_PREFIX + jwtService.extractRole(token));
        var authentication = new UsernamePasswordAuthenticationToken(
                jwtService.extractUsername(token), null, List.of(authority));
        SecurityContextHolder.getContext().setAuthentication(authentication);
    }
}
