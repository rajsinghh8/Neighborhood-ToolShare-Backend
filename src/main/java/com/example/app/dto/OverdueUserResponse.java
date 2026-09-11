package com.example.app.dto;

public class OverdueUserResponse {

  private Long userId;

  private String name;

  private String email;

  private long overdueCount;

  public OverdueUserResponse(Long userId, String name, String email, long overdueCount) {
    this.userId = userId;
    this.name = name;
    this.email = email;
    this.overdueCount = overdueCount;
  }

  public Long getUserId() {
    return userId;
  }

  public String getName() {
    return name;
  }

  public String getEmail() {
    return email;
  }

  public long getOverdueCount() {
    return overdueCount;
  }
}
