package com.school.sms.service;

import com.school.sms.config.JwtProperties;
import com.school.sms.dto.Dtos.LoginRequest;
import com.school.sms.dto.Dtos.RefreshRequest;
import com.school.sms.dto.Dtos.RegisterRequest;
import com.school.sms.dto.Dtos.TokenResponse;
import com.school.sms.exception.ConflictException;
import com.school.sms.exception.InvalidCredentialsException;
import com.school.sms.model.AppUser;
import com.school.sms.model.RefreshToken;
import com.school.sms.repository.RefreshTokenRepository;
import com.school.sms.repository.UserRepository;
import com.school.sms.security.JwtService;
import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.util.Base64;
import java.util.Optional;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Login, refresh-token rotation and user registration. */
@Service
public class AuthService {

    private static final Logger LOG = LoggerFactory.getLogger(AuthService.class);

    private static final String TOKEN_TYPE = "Bearer";
    private static final int REFRESH_TOKEN_BYTES = 48;
    private static final String INVALID_CREDENTIALS = "Invalid credentials";
    private static final String INVALID_REFRESH_TOKEN = "Invalid refresh token";
    private static final String USERNAME_EXISTS = "Username already exists";

    private final UserRepository userRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final Duration refreshTtl;
    private final SecureRandom secureRandom = new SecureRandom();
    /** Hash checked when the username is unknown, so response time does not reveal which users exist. */
    private final String decoyPasswordHash;

    public AuthService(UserRepository userRepository,
                       RefreshTokenRepository refreshTokenRepository,
                       PasswordEncoder passwordEncoder,
                       JwtService jwtService,
                       JwtProperties jwtProperties) {
        this.userRepository = userRepository;
        this.refreshTokenRepository = refreshTokenRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.refreshTtl = Duration.ofDays(jwtProperties.refreshExpiryDays());
        this.decoyPasswordHash = passwordEncoder.encode(UUID.randomUUID().toString());
    }

    @Transactional
    public TokenResponse login(LoginRequest request) {
        Optional<AppUser> candidate = userRepository.findByUsername(request.username());
        String hashToCheck = candidate.map(AppUser::getPasswordHash).orElse(decoyPasswordHash);
        boolean passwordMatches = passwordEncoder.matches(request.password(), hashToCheck);
        AppUser user = candidate
                .filter(found -> passwordMatches)
                .orElseThrow(() -> new InvalidCredentialsException(INVALID_CREDENTIALS));
        LOG.info("User logged in [userId={}, username={}]", user.getId(), user.getUsername());
        return issueTokens(user);
    }

    /** Expired-token cleanup must survive the rejection, hence no rollback for credential errors. */
    @Transactional(noRollbackFor = InvalidCredentialsException.class)
    public TokenResponse refresh(RefreshRequest request) {
        RefreshToken stored = refreshTokenRepository.findByToken(request.refreshToken())
                .orElseThrow(() -> new InvalidCredentialsException(INVALID_REFRESH_TOKEN));
        refreshTokenRepository.delete(stored);
        if (stored.isExpired(Instant.now())) {
            throw new InvalidCredentialsException(INVALID_REFRESH_TOKEN);
        }
        return issueTokens(stored.getUser());
    }

    @Transactional
    public void register(RegisterRequest request) {
        if (userRepository.existsByUsername(request.username())) {
            throw new ConflictException(USERNAME_EXISTS);
        }
        AppUser user = new AppUser(request.username(),
                passwordEncoder.encode(request.password()), request.role());
        try {
            userRepository.saveAndFlush(user);
        } catch (DataIntegrityViolationException ex) {
            throw new ConflictException(USERNAME_EXISTS, ex);
        }
        LOG.info("User registered [userId={}, username={}, role={}]",
                user.getId(), user.getUsername(), user.getRole());
    }

    private TokenResponse issueTokens(AppUser user) {
        String refreshToken = generateRefreshTokenValue();
        refreshTokenRepository.save(new RefreshToken(refreshToken, Instant.now().plus(refreshTtl), user));
        return new TokenResponse(jwtService.generateAccessToken(user), refreshToken,
                TOKEN_TYPE, jwtService.accessTokenTtlSeconds());
    }

    private String generateRefreshTokenValue() {
        byte[] bytes = new byte[REFRESH_TOKEN_BYTES];
        secureRandom.nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }
}
