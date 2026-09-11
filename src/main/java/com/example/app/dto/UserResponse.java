package com.example.app.dto;

import java.time.LocalDateTime;

public class UserResponse {

  private Long id;

  private String name;

  private String email;

  private String neighborhood;

  private String phone;

  private String apiKey;

  private LocalDateTime createdAt;

  public UserResponse(
      Long id,
      String name,
      String email,
      String neighborhood,
      String phone,
      String apiKey,
      LocalDateTime createdAt) {
    this.id = id;
    this.name = name;
    this.email = email;
    this.neighborhood = neighborhood;
    this.phone = phone;
    this.apiKey = apiKey;
    this.createdAt = createdAt;
  }

  public Long getId() {
    return id;
  }

  public String getName() {
    return name;
  }

  public String getEmail() {
    return email;
  }

  public String getNeighborhood() {
    return neighborhood;
  }

  public String getPhone() {
    return phone;
  }

  public String getApiKey() {
    return apiKey;
  }

  public LocalDateTime getCreatedAt() {
    return createdAt;
  }
}
