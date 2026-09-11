package com.example.app.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EntityListeners;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.LocalDate;
import java.time.LocalDateTime;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

@Entity
@Table(name = "borrow_requests")
@EntityListeners(AuditingEntityListener.class)
public class BorrowRequest {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "tool_id", nullable = false)
  private Tool tool;

  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "borrower_id", nullable = false)
  private User borrower;

  @Column(name = "requested_start_date", nullable = false)
  private LocalDate requestedStartDate;

  @Column(name = "requested_end_date", nullable = false)
  private LocalDate requestedEndDate;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false)
  private BorrowStatus status = BorrowStatus.PENDING;

  @CreatedDate
  @Column(name = "created_at", nullable = false, updatable = false)
  private LocalDateTime createdAt;

  @LastModifiedDate
  @Column(name = "updated_at")
  private LocalDateTime updatedAt;

  public Long getId() {
    return id;
  }

  public void setId(Long id) {
    this.id = id;
  }

  public Tool getTool() {
    return tool;
  }

  public void setTool(Tool tool) {
    this.tool = tool;
  }

  public User getBorrower() {
    return borrower;
  }

  public void setBorrower(User borrower) {
    this.borrower = borrower;
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

  public BorrowStatus getStatus() {
    return status;
  }

  public void setStatus(BorrowStatus status) {
    this.status = status;
  }

  public LocalDateTime getCreatedAt() {
    return createdAt;
  }

  public void setCreatedAt(LocalDateTime createdAt) {
    this.createdAt = createdAt;
  }

  public LocalDateTime getUpdatedAt() {
    return updatedAt;
  }

  public void setUpdatedAt(LocalDateTime updatedAt) {
    this.updatedAt = updatedAt;
  }
}
