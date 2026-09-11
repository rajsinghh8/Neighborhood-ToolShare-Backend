package com.example.app.dto;

import com.example.app.entity.BorrowStatus;
import java.time.LocalDate;
import java.time.LocalDateTime;

public class BorrowRequestResponse {

  private Long id;

  private Long toolId;

  private String toolName;

  private Long ownerId;

  private Long borrowerId;

  private String borrowerName;

  private LocalDate requestedStartDate;

  private LocalDate requestedEndDate;

  private BorrowStatus status;

  private LocalDateTime createdAt;

  public BorrowRequestResponse(
      Long id,
      Long toolId,
      String toolName,
      Long ownerId,
      Long borrowerId,
      String borrowerName,
      LocalDate requestedStartDate,
      LocalDate requestedEndDate,
      BorrowStatus status,
      LocalDateTime createdAt) {
    this.id = id;
    this.toolId = toolId;
    this.toolName = toolName;
    this.ownerId = ownerId;
    this.borrowerId = borrowerId;
    this.borrowerName = borrowerName;
    this.requestedStartDate = requestedStartDate;
    this.requestedEndDate = requestedEndDate;
    this.status = status;
    this.createdAt = createdAt;
  }

  public Long getId() {
    return id;
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

  public Long getBorrowerId() {
    return borrowerId;
  }

  public String getBorrowerName() {
    return borrowerName;
  }

  public LocalDate getRequestedStartDate() {
    return requestedStartDate;
  }

  public LocalDate getRequestedEndDate() {
    return requestedEndDate;
  }

  public BorrowStatus getStatus() {
    return status;
  }

  public LocalDateTime getCreatedAt() {
    return createdAt;
  }
}
