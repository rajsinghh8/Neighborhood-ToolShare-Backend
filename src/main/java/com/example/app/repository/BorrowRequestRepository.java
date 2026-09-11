package com.example.app.repository;

import com.example.app.entity.BorrowRequest;
import com.example.app.entity.BorrowStatus;
import java.util.List;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface BorrowRequestRepository extends JpaRepository<BorrowRequest, Long> {

  Page<BorrowRequest> findByBorrowerId(Long borrowerId, Pageable pageable);

  Page<BorrowRequest> findByTool_Owner_Id(Long ownerId, Pageable pageable);

  List<BorrowRequest> findByStatus(BorrowStatus status);

  long countByBorrowerIdAndStatus(Long borrowerId, BorrowStatus status);
}
