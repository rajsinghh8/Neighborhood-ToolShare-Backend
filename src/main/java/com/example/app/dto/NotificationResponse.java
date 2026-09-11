package com.example.app.dto;

import com.example.app.entity.NotificationType;
import java.time.LocalDateTime;

public class NotificationResponse {

  private Long id;

  private String message;

  private NotificationType type;

  private boolean read;

  private LocalDateTime createdAt;

  public NotificationResponse(
      Long id, String message, NotificationType type, boolean read, LocalDateTime createdAt) {
    this.id = id;
    this.message = message;
    this.type = type;
    this.read = read;
    this.createdAt = createdAt;
  }

  public Long getId() {
    return id;
  }

  public String getMessage() {
    return message;
  }

  public NotificationType getType() {
    return type;
  }

  public boolean isRead() {
    return read;
  }

  public LocalDateTime getCreatedAt() {
    return createdAt;
  }
}
