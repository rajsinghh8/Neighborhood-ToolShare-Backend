package com.example.app.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

public class ReviewRequest {

  @NotNull(message = "reservationId is required")
  private Long reservationId;

  @NotNull(message = "revieweeId is required")
  private Long revieweeId;

  @NotNull(message = "rating is required")
  @Min(value = 1, message = "rating must be between 1 and 5")
  @Max(value = 5, message = "rating must be between 1 and 5")
  private Integer rating;

  private String comment;

  public Long getReservationId() {
    return reservationId;
  }

  public void setReservationId(Long reservationId) {
    this.reservationId = reservationId;
  }

  public Long getRevieweeId() {
    return revieweeId;
  }

  public void setRevieweeId(Long revieweeId) {
    this.revieweeId = revieweeId;
  }

  public Integer getRating() {
    return rating;
  }

  public void setRating(Integer rating) {
    this.rating = rating;
  }

  public String getComment() {
    return comment;
  }

  public void setComment(String comment) {
    this.comment = comment;
  }
}
