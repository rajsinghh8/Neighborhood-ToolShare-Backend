package com.example.app.dto;

import java.time.LocalDateTime;

public class ReviewResponse {

  private Long id;

  private Long reservationId;

  private Long reviewerId;

  private String reviewerName;

  private Long revieweeId;

  private String revieweeName;

  private Integer rating;

  private String comment;

  private LocalDateTime createdAt;

  public ReviewResponse(
      Long id,
      Long reservationId,
      Long reviewerId,
      String reviewerName,
      Long revieweeId,
      String revieweeName,
      Integer rating,
      String comment,
      LocalDateTime createdAt) {
    this.id = id;
    this.reservationId = reservationId;
    this.reviewerId = reviewerId;
    this.reviewerName = reviewerName;
    this.revieweeId = revieweeId;
    this.revieweeName = revieweeName;
    this.rating = rating;
    this.comment = comment;
    this.createdAt = createdAt;
  }

  public Long getId() {
    return id;
  }

  public Long getReservationId() {
    return reservationId;
  }

  public Long getReviewerId() {
    return reviewerId;
  }

  public String getReviewerName() {
    return reviewerName;
  }

  public Long getRevieweeId() {
    return revieweeId;
  }

  public String getRevieweeName() {
    return revieweeName;
  }

  public Integer getRating() {
    return rating;
  }

  public String getComment() {
    return comment;
  }

  public LocalDateTime getCreatedAt() {
    return createdAt;
  }
}
