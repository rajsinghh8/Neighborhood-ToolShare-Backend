package com.example.app.dto;

import com.example.app.entity.BorrowStatus;
import java.time.LocalDate;
import java.time.LocalDateTime;

public class BorrowRequestResponse {

  private Long id;

  private Long toolId;

  private String toolName;

  private Long ownerId;

  private String ownerName;

  private Long borrowerId;

  private String borrowerName;

  private LocalDate requestedStartDate;

  private LocalDate requestedEndDate;

  private BorrowStatus status;

  private LocalDateTime createdAt;

  /**
   * Contact details for the tool owner and borrower, populated once the request has been
   * approved so both parties can coordinate pickup/return. Left null while the request is
   * pending or rejected.
   */
  private String ownerContactEmail;

  private String ownerContactPhone;

  private String borrowerContactEmail;

  private String borrowerContactPhone;

  public BorrowRequestResponse(
      Long id,
      Long toolId,
      String toolName,
      Long ownerId,
      String ownerName,
      Long borrowerId,
      String borrowerName,
      LocalDate requestedStartDate,
      LocalDate requestedEndDate,
      BorrowStatus status,
      LocalDateTime createdAt,
      String ownerContactEmail,
      String ownerContactPhone,
      String borrowerContactEmail,
      String borrowerContactPhone) {
    this.id = id;
    this.toolId = toolId;
    this.toolName = toolName;
    this.ownerId = ownerId;
    this.ownerName = ownerName;
    this.borrowerId = borrowerId;
    this.borrowerName = borrowerName;
    this.requestedStartDate = requestedStartDate;
    this.requestedEndDate = requestedEndDate;
    this.status = status;
    this.createdAt = createdAt;
    this.ownerContactEmail = ownerContactEmail;
    this.ownerContactPhone = ownerContactPhone;
    this.borrowerContactEmail = borrowerContactEmail;
    this.borrowerContactPhone = borrowerContactPhone;
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

  public String getOwnerName() {
    return ownerName;
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

  public String getOwnerContactEmail() {
    return ownerContactEmail;
  }

  public String getOwnerContactPhone() {
    return ownerContactPhone;
  }

  public String getBorrowerContactEmail() {
    return borrowerContactEmail;
  }

  public String getBorrowerContactPhone() {
    return borrowerContactPhone;
  }
}
