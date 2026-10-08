package com.school.sms.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/** Bound from {@code app.jwt.*}. */
@ConfigurationProperties(prefix = "app.jwt")
public record JwtProperties(String secret, long accessExpiryMinutes, long refreshExpiryDays) {
}
