package com.example.app.repository;

import com.example.app.entity.Reservation;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ReservationRepository extends JpaRepository<Reservation, Long> {

  Optional<Reservation> findByBorrowRequestId(Long borrowRequestId);

  Page<Reservation> findByBorrowRequest_Borrower_Id(Long borrowerId, Pageable pageable);

  Page<Reservation> findByBorrowRequest_Tool_Owner_Id(Long ownerId, Pageable pageable);
}
