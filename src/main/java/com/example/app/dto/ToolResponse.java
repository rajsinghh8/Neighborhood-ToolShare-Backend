package com.example.app.dto;

import com.example.app.entity.ToolCondition;
import java.time.LocalDateTime;

public class ToolResponse {

  private Long id;

  private String name;

  private String category;

  private String description;

  private ToolCondition condition;

  private boolean available;

  private Long ownerId;

  private String ownerName;

  private String ownerNeighborhood;

  private LocalDateTime createdAt;

  public ToolResponse(
      Long id,
      String name,
      String category,
      String description,
      ToolCondition condition,
      boolean available,
      Long ownerId,
      String ownerName,
      String ownerNeighborhood,
      LocalDateTime createdAt) {
    this.id = id;
    this.name = name;
    this.category = category;
    this.description = description;
    this.condition = condition;
    this.available = available;
    this.ownerId = ownerId;
    this.ownerName = ownerName;
    this.ownerNeighborhood = ownerNeighborhood;
    this.createdAt = createdAt;
  }

  public Long getId() {
    return id;
  }

  public String getName() {
    return name;
  }

  public String getCategory() {
    return category;
  }

  public String getDescription() {
    return description;
  }

  public ToolCondition getCondition() {
    return condition;
  }

  public boolean isAvailable() {
    return available;
  }

  public Long getOwnerId() {
    return ownerId;
  }

  public String getOwnerName() {
    return ownerName;
  }

  public String getOwnerNeighborhood() {
    return ownerNeighborhood;
  }

  public LocalDateTime getCreatedAt() {
    return createdAt;
  }
}
