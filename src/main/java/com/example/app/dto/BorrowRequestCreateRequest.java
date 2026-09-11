package com.example.app.dto;

import jakarta.validation.constraints.FutureOrPresent;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;

public class BorrowRequestCreateRequest {

  @NotNull(message = "toolId is required")
  private Long toolId;

  @NotNull(message = "requestedStartDate is required")
  @FutureOrPresent(message = "requestedStartDate must be today or in the future")
  private LocalDate requestedStartDate;

  @NotNull(message = "requestedEndDate is required")
  private LocalDate requestedEndDate;

  public Long getToolId() {
    return toolId;
  }

  public void setToolId(Long toolId) {
    this.toolId = toolId;
  }

  public LocalDate getRequestedStartDate() {
    return requestedStartDate;
  }

  public void setRequestedStartDate(LocalDate requestedStartDate) {
    this.requestedStartDate = requestedStartDate;
  }

  public LocalDate getRequestedEndDate() {
    return requestedEndDate;
  }

  public void setRequestedEndDate(LocalDate requestedEndDate) {
    this.requestedEndDate = requestedEndDate;
  }
}
