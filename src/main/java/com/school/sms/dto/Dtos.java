package com.school.sms.dto;

import com.school.sms.model.Role;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Past;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;
import java.util.List;

/** Request/response wire types. JPA entities are never exposed directly. */
public final class Dtos {

    public static final int MIN_GRADE = 1;
    public static final int MAX_GRADE = 12;

    private Dtos() {
    }

    public record LoginRequest(
            @NotBlank String username,
            @NotBlank String password) {
    }

    public record RefreshRequest(@NotBlank String refreshToken) {
    }

    public record RegisterRequest(
            @NotBlank @Size(min = 3, max = 64) String username,
            @NotBlank @Size(min = 8, max = 128) String password,
            @NotNull Role role) {
    }

    public record TokenResponse(
            String accessToken,
            String refreshToken,
            String tokenType,
            long expiresInSeconds) {
    }

    public record StudentRequest(
            @NotBlank @Size(max = 100) String firstName,
            @NotBlank @Size(max = 100) String lastName,
            @NotNull @Past LocalDate dateOfBirth,
            @NotNull @Min(MIN_GRADE) @Max(MAX_GRADE) Integer gradeLevel,
            @Size(max = 20) String section,
            @Size(max = 200) String guardianName,
            @Size(max = 30) String guardianPhone,
            @NotNull Boolean active) {
    }

    public record StudentResponse(
            Long id,
            String firstName,
            String lastName,
            LocalDate dateOfBirth,
            Integer gradeLevel,
            String section,
            String guardianName,
            String guardianPhone,
            boolean active) {
    }

    public record PageResponse<T>(List<T> items, int offset, int limit, long total) {
    }
}
