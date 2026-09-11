package com.example.app.controller;

import com.example.app.dto.ReviewRequest;
import com.example.app.dto.ReviewResponse;
import com.example.app.entity.User;
import com.example.app.service.ReviewService;
import com.example.app.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/reviews")
@Tag(name = "Reviews", description = "Ratings and comments exchanged after a completed borrow")
public class ReviewController {

  private final ReviewService reviewService;

  private final UserService userService;

  public ReviewController(ReviewService reviewService, UserService userService) {
    this.reviewService = reviewService;
    this.userService = userService;
  }

  @PostMapping
  @Operation(summary = "Leave a review/rating for the other participant of a completed reservation")
  public ResponseEntity<ReviewResponse> create(
      Authentication authentication, @Valid @RequestBody ReviewRequest request) {
    User reviewer = userService.getByEmail(authentication.getName());
    return ResponseEntity.status(HttpStatus.CREATED).body(reviewService.create(reviewer, request));
  }

  @GetMapping("/user/{userId}")
  @Operation(summary = "List reviews received by a given user (paginated)")
  public ResponseEntity<Page<ReviewResponse>> getReviewsForUser(
      @PathVariable Long userId, @PageableDefault(size = 20) Pageable pageable) {
    return ResponseEntity.ok(reviewService.getReviewsForUser(userId, pageable));
  }

  @GetMapping("/{id}")
  @Operation(summary = "Get a single review by id")
  public ResponseEntity<ReviewResponse> getById(@PathVariable Long id) {
    return ResponseEntity.ok(reviewService.getById(id));
  }
}
