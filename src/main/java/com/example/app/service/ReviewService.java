package com.example.app.service;

import com.example.app.dto.ReviewRequest;
import com.example.app.dto.ReviewResponse;
import com.example.app.entity.BorrowRequest;
import com.example.app.entity.BorrowStatus;
import com.example.app.entity.Reservation;
import com.example.app.entity.Review;
import com.example.app.entity.User;
import com.example.app.exception.BadRequestException;
import com.example.app.exception.ForbiddenException;
import com.example.app.exception.ResourceNotFoundException;
import com.example.app.repository.ReviewRepository;
import com.example.app.repository.UserRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ReviewService {

  private final ReviewRepository reviewRepository;

  private final UserRepository userRepository;

  private final ReservationService reservationService;

  public ReviewService(
      ReviewRepository reviewRepository,
      UserRepository userRepository,
      ReservationService reservationService) {
    this.reviewRepository = reviewRepository;
    this.userRepository = userRepository;
    this.reservationService = reservationService;
  }

  @Transactional
  public ReviewResponse create(User reviewer, ReviewRequest request) {
    Reservation reservation = reservationService.getEntityById(request.getReservationId());
    BorrowRequest borrowRequest = reservation.getBorrowRequest();

    if (borrowRequest.getStatus() != BorrowStatus.RETURNED) {
      throw new BadRequestException("Reviews can only be left after the tool has been returned");
    }

    Long borrowerId = borrowRequest.getBorrower().getId();
    Long ownerId = borrowRequest.getTool().getOwner().getId();

    if (!reviewer.getId().equals(borrowerId) && !reviewer.getId().equals(ownerId)) {
      throw new ForbiddenException("You are not part of this reservation");
    }

    Long expectedRevieweeId = reviewer.getId().equals(borrowerId) ? ownerId : borrowerId;
    if (!expectedRevieweeId.equals(request.getRevieweeId())) {
      throw new BadRequestException("revieweeId must be the other participant in this reservation");
    }

    if (reviewRepository.existsByReservationIdAndReviewerId(
        reservation.getId(), reviewer.getId())) {
      throw new BadRequestException("You have already reviewed this reservation");
    }

    User reviewee =
        userRepository
            .findById(request.getRevieweeId())
            .orElseThrow(
                () ->
                    new ResourceNotFoundException(
                        "User not found with id: " + request.getRevieweeId()));

    Review review = new Review();
    review.setReservation(reservation);
    review.setReviewer(reviewer);
    review.setReviewee(reviewee);
    review.setRating(request.getRating());
    review.setComment(request.getComment());
    Review saved = reviewRepository.save(review);
    return toResponse(saved);
  }

  @Transactional(readOnly = true)
  public Page<ReviewResponse> getReviewsForUser(Long revieweeId, Pageable pageable) {
    return reviewRepository.findByRevieweeId(revieweeId, pageable).map(this::toResponse);
  }

  @Transactional(readOnly = true)
  public ReviewResponse getById(Long id) {
    Review review =
        reviewRepository
            .findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Review not found with id: " + id));
    return toResponse(review);
  }

  public ReviewResponse toResponse(Review review) {
    return new ReviewResponse(
        review.getId(),
        review.getReservation().getId(),
        review.getReviewer().getId(),
        review.getReviewer().getName(),
        review.getReviewee().getId(),
        review.getReviewee().getName(),
        review.getRating(),
        review.getComment(),
        review.getCreatedAt());
  }
}
