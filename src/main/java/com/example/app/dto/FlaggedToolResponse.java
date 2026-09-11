package com.example.app.dto;

public class FlaggedToolResponse {

  private Long toolId;

  private String toolName;

  private Long ownerId;

  private String ownerName;

  private long overdueCount;

  public FlaggedToolResponse(
      Long toolId, String toolName, Long ownerId, String ownerName, long overdueCount) {
    this.toolId = toolId;
    this.toolName = toolName;
    this.ownerId = ownerId;
    this.ownerName = ownerName;
    this.overdueCount = overdueCount;
  }

  public Long getToolId() {
    return toolId;
  }

  public String getToolName() {
    return toolName;
  }

  public Long getOwnerId() {
    return ownerId;
  }

  public String getOwnerName() {
    return ownerName;
  }

  public long getOverdueCount() {
    return overdueCount;
  }
}
