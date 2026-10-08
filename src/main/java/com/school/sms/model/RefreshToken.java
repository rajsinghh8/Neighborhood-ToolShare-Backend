package com.school.sms.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.Instant;

/** A long-lived, single-use credential exchanged for a new access token. */
@Entity
@Table(name = "REFRESH_TOKEN")
public class RefreshToken {

    private static final int TOKEN_LENGTH = 100;

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "TOKEN", nullable = false, unique = true, length = TOKEN_LENGTH)
    private String token;

    @Column(name = "EXPIRES_AT", nullable = false)
    private Instant expiresAt;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "USER_ID", nullable = false)
    private AppUser user;

    protected RefreshToken() {
        // required by JPA
    }

    public RefreshToken(String token, Instant expiresAt, AppUser user) {
        this.token = token;
        this.expiresAt = expiresAt;
        this.user = user;
    }

    public AppUser getUser() {
        return user;
    }

    public boolean isExpired(Instant now) {
        return !expiresAt.isAfter(now);
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof RefreshToken that)) {
            return false;
        }
        return id != null && id.equals(that.id);
    }

    @Override
    public int hashCode() {
        return getClass().hashCode();
    }
}
