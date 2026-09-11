package com.example.app.service;

import com.example.app.dto.FlaggedToolResponse;
import com.example.app.dto.OverdueUserResponse;
import com.example.app.entity.BorrowRequest;
import com.example.app.entity.BorrowStatus;
import com.example.app.repository.BorrowRequestRepository;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AdminService {

  private final BorrowRequestRepository borrowRequestRepository;

  public AdminService(BorrowRequestRepository borrowRequestRepository) {
    this.borrowRequestRepository = borrowRequestRepository;
  }

  @Transactional(readOnly = true)
  public List<OverdueUserResponse> getRepeatedlyOverdueUsers(int minOverdueCount) {
    List<BorrowRequest> overdueRequests =
        borrowRequestRepository.findByStatus(BorrowStatus.OVERDUE);

    Map<Long, List<BorrowRequest>> byBorrower =
        overdueRequests.stream().collect(Collectors.groupingBy(br -> br.getBorrower().getId()));

    return byBorrower.entrySet().stream()
        .filter(entry -> entry.getValue().size() >= minOverdueCount)
        .map(
            entry -> {
              BorrowRequest sample = entry.getValue().get(0);
              return new OverdueUserResponse(
                  sample.getBorrower().getId(),
                  sample.getBorrower().getName(),
                  sample.getBorrower().getEmail(),
                  entry.getValue().size());
            })
        .sorted(Comparator.comparingLong(OverdueUserResponse::getOverdueCount).reversed())
        .collect(Collectors.toList());
  }

  @Transactional(readOnly = true)
  public List<FlaggedToolResponse> getFlaggedTools(int minOverdueCount) {
    List<BorrowRequest> overdueRequests =
        borrowRequestRepository.findByStatus(BorrowStatus.OVERDUE);

    Map<Long, List<BorrowRequest>> byTool =
        overdueRequests.stream().collect(Collectors.groupingBy(br -> br.getTool().getId()));

    return byTool.entrySet().stream()
        .filter(entry -> entry.getValue().size() >= minOverdueCount)
        .map(
            entry -> {
              BorrowRequest sample = entry.getValue().get(0);
              return new FlaggedToolResponse(
                  sample.getTool().getId(),
                  sample.getTool().getName(),
                  sample.getTool().getOwner().getId(),
                  sample.getTool().getOwner().getName(),
                  entry.getValue().size());
            })
        .sorted(Comparator.comparingLong(FlaggedToolResponse::getOverdueCount).reversed())
        .collect(Collectors.toList());
  }
}
