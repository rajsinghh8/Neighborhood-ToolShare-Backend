package com.school.sms.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/** Bound from {@code app.admin.*}: credentials of the default administrator seeded on startup. */
@ConfigurationProperties(prefix = "app.admin")
public record AdminProperties(String username, String password) {
}
