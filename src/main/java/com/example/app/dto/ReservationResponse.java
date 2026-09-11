package com.example.app.dto;

import java.time.LocalDate;
import java.time.LocalDateTime;

public class ReservationResponse {

  private Long id;

  private Long borrowRequestId;

  private Long toolId;

  private String toolName;

  private Long borrowerId;

  private LocalDate startDate;

  private LocalDate endDate;

  private String pickupNotes;

  private String returnNotes;

  private LocalDateTime createdAt;

  public ReservationResponse(
      Long id,
      Long borrowRequestId,
      Long toolId,
      String toolName,
      Long borrowerId,
      LocalDate startDate,
      LocalDate endDate,
      String pickupNotes,
      String returnNotes,
      LocalDateTime createdAt) {
    this.id = id;
    this.borrowRequestId = borrowRequestId;
    this.toolId = toolId;
    this.toolName = toolName;
    this.borrowerId = borrowerId;
    this.startDate = startDate;
    this.endDate = endDate;
    this.pickupNotes = pickupNotes;
    this.returnNotes = returnNotes;
    this.createdAt = createdAt;
  }

  public Long getId() {
    return id;
  }

  public Long getBorrowRequestId() {
    return borrowRequestId;
  }

  public Long getToolId() {
    return toolId;
  }

  public String getToolName() {
    return toolName;
  }

  public Long getBorrowerId() {
    return borrowerId;
  }

  public LocalDate getStartDate() {
    return startDate;
  }

  public LocalDate getEndDate() {
    return endDate;
  }

  public String getPickupNotes() {
    return pickupNotes;
  }

  public String getReturnNotes() {
    return returnNotes;
  }

  public LocalDateTime getCreatedAt() {
    return createdAt;
  }
}
