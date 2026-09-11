package com.example.app.dto;

public class JwtResponse {

  private String token;

  private String apiKey;

  private Long userId;

  private String name;

  private String email;

  public JwtResponse(String token, String apiKey, Long userId, String name, String email) {
    this.token = token;
    this.apiKey = apiKey;
    this.userId = userId;
    this.name = name;
    this.email = email;
  }

  public String getToken() {
    return token;
  }

  public void setToken(String token) {
    this.token = token;
  }

  public String getApiKey() {
    return apiKey;
  }

  public void setApiKey(String apiKey) {
    this.apiKey = apiKey;
  }

  public Long getUserId() {
    return userId;
  }

  public void setUserId(Long userId) {
    this.userId = userId;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public String getEmail() {
    return email;
  }

  public void setEmail(String email) {
    this.email = email;
  }
}
