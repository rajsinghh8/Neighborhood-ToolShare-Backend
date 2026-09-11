package com.example.app.repository;

import com.example.app.entity.Review;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ReviewRepository extends JpaRepository<Review, Long> {

  Page<Review> findByRevieweeId(Long revieweeId, Pageable pageable);

  Page<Review> findByReviewerId(Long reviewerId, Pageable pageable);

  boolean existsByReservationIdAndReviewerId(Long reservationId, Long reviewerId);
}
