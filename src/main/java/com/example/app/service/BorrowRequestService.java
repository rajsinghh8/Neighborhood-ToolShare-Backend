package com.example.app.service;

import com.example.app.dto.BorrowRequestCreateRequest;
import com.example.app.dto.BorrowRequestResponse;
import com.example.app.entity.BorrowRequest;
import com.example.app.entity.BorrowStatus;
import com.example.app.entity.NotificationType;
import com.example.app.entity.Reservation;
import com.example.app.entity.Tool;
import com.example.app.entity.User;
import com.example.app.exception.BadRequestException;
import com.example.app.exception.ForbiddenException;
import com.example.app.exception.ResourceNotFoundException;
import com.example.app.repository.BorrowRequestRepository;
import com.example.app.repository.ReservationRepository;
import java.time.LocalDate;
import java.util.List;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class BorrowRequestService {

  private final BorrowRequestRepository borrowRequestRepository;

  private final ReservationRepository reservationRepository;

  private final ToolService toolService;

  private final ReservationService reservationService;

  private final NotificationService notificationService;

  public BorrowRequestService(
      BorrowRequestRepository borrowRequestRepository,
      ReservationRepository reservationRepository,
      ToolService toolService,
      ReservationService reservationService,
      NotificationService notificationService) {
    this.borrowRequestRepository = borrowRequestRepository;
    this.reservationRepository = reservationRepository;
    this.toolService = toolService;
    this.reservationService = reservationService;
    this.notificationService = notificationService;
  }

  @Transactional
  public BorrowRequestResponse create(User borrower, BorrowRequestCreateRequest request) {
    Tool tool = toolService.getEntityById(request.getToolId());

    if (tool.getOwner().getId().equals(borrower.getId())) {
      throw new BadRequestException("You cannot borrow your own tool");
    }
    if (!tool.isAvailable()) {
      throw new BadRequestException("Tool is not available for borrowing");
    }
    if (request.getRequestedEndDate().isBefore(request.getRequestedStartDate())) {
      throw new BadRequestException("requestedEndDate must not be before requestedStartDate");
    }

    BorrowRequest borrowRequest = new BorrowRequest();
    borrowRequest.setTool(tool);
    borrowRequest.setBorrower(borrower);
    borrowRequest.setRequestedStartDate(request.getRequestedStartDate());
    borrowRequest.setRequestedEndDate(request.getRequestedEndDate());
    borrowRequest.setStatus(BorrowStatus.PENDING);
    BorrowRequest saved = borrowRequestRepository.save(borrowRequest);

    notificationService.notify(
        tool.getOwner(),
        "New borrow request for your tool '" + tool.getName() + "' from " + borrower.getName(),
        NotificationType.NEW_REQUEST);

    return toResponse(saved);
  }

  @Transactional(readOnly = true)
  public Page<BorrowRequestResponse> getMyRequestsAsBorrower(Long borrowerId, Pageable pageable) {
    return borrowRequestRepository.findByBorrowerId(borrowerId, pageable).map(this::toResponse);
  }

  @Transactional(readOnly = true)
  public Page<BorrowRequestResponse> getMyRequestsAsOwner(Long ownerId, Pageable pageable) {
    return borrowRequestRepository.findByTool_Owner_Id(ownerId, pageable).map(this::toResponse);
  }

  @Transactional(readOnly = true)
  public BorrowRequest getEntityById(Long id) {
    return borrowRequestRepository
        .findById(id)
        .orElseThrow(
            () -> new ResourceNotFoundException("Borrow request not found with id: " + id));
  }

  @Transactional(readOnly = true)
  public BorrowRequestResponse getById(Long id, User currentUser) {
    BorrowRequest borrowRequest = getEntityById(id);
    assertParticipant(borrowRequest, currentUser);
    return toResponse(borrowRequest);
  }

  @Transactional
  public BorrowRequestResponse approve(Long id, User currentUser) {
    BorrowRequest borrowRequest = getEntityById(id);
    assertOwner(borrowRequest, currentUser);
    if (borrowRequest.getStatus() != BorrowStatus.PENDING) {
      throw new BadRequestException("Only pending requests can be approved");
    }
    borrowRequest.setStatus(BorrowStatus.APPROVED);
    BorrowRequest saved = borrowRequestRepository.save(borrowRequest);

    reservationService.createReservation(saved);

    Tool tool = saved.getTool();
    tool.setAvailable(false);
    toolService.updateAvailabilityDirect(tool, false);

    notificationService.notify(
        saved.getBorrower(),
        "Your request for '" + saved.getTool().getName() + "' was approved",
        NotificationType.APPROVED);

    return toResponse(saved);
  }

  @Transactional
  public BorrowRequestResponse reject(Long id, User currentUser) {
    BorrowRequest borrowRequest = getEntityById(id);
    assertOwner(borrowRequest, currentUser);
    if (borrowRequest.getStatus() != BorrowStatus.PENDING) {
      throw new BadRequestException("Only pending requests can be rejected");
    }
    borrowRequest.setStatus(BorrowStatus.REJECTED);
    BorrowRequest saved = borrowRequestRepository.save(borrowRequest);

    notificationService.notify(
        saved.getBorrower(),
        "Your request for '" + saved.getTool().getName() + "' was rejected",
        NotificationType.REJECTED);

    return toResponse(saved);
  }

  @Transactional
  public BorrowRequestResponse activate(Long id, User currentUser) {
    BorrowRequest borrowRequest = getEntityById(id);
    assertParticipant(borrowRequest, currentUser);
    if (borrowRequest.getStatus() != BorrowStatus.APPROVED) {
      throw new BadRequestException("Only approved requests can be activated");
    }
    borrowRequest.setStatus(BorrowStatus.ACTIVE);
    BorrowRequest saved = borrowRequestRepository.save(borrowRequest);
    return toResponse(saved);
  }

  @Transactional
  public BorrowRequestResponse markReturned(Long id, User currentUser) {
    BorrowRequest borrowRequest = getEntityById(id);
    assertParticipant(borrowRequest, currentUser);
    if (borrowRequest.getStatus() != BorrowStatus.ACTIVE
        && borrowRequest.getStatus() != BorrowStatus.OVERDUE) {
      throw new BadRequestException("Only active or overdue requests can be marked returned");
    }
    borrowRequest.setStatus(BorrowStatus.RETURNED);
    BorrowRequest saved = borrowRequestRepository.save(borrowRequest);

    Tool tool = saved.getTool();
    toolService.updateAvailabilityDirect(tool, true);

    notificationService.notify(
        saved.getTool().getOwner(),
        "'"
            + saved.getTool().getName()
            + "' has been marked as returned by "
            + saved.getBorrower().getName(),
        NotificationType.RETURNED);

    return toResponse(saved);
  }

  @Scheduled(fixedRate = 300000)
  @Transactional
  public void flagOverdueRequests() {
    List<BorrowRequest> activeRequests = borrowRequestRepository.findByStatus(BorrowStatus.ACTIVE);
    LocalDate today = LocalDate.now();
    for (BorrowRequest borrowRequest : activeRequests) {
      Reservation reservation =
          reservationRepository.findByBorrowRequestId(borrowRequest.getId()).orElse(null);
      LocalDate dueDate =
          reservation != null ? reservation.getEndDate() : borrowRequest.getRequestedEndDate();
      if (dueDate.isBefore(today)) {
        borrowRequest.setStatus(BorrowStatus.OVERDUE);
        borrowRequestRepository.save(borrowRequest);
        notificationService.notify(
            borrowRequest.getBorrower(),
            "'"
                + borrowRequest.getTool().getName()
                + "' is overdue. Please return it as soon as possible.",
            NotificationType.OVERDUE);
        notificationService.notify(
            borrowRequest.getTool().getOwner(),
            "Your tool '"
                + borrowRequest.getTool().getName()
                + "' is overdue with "
                + borrowRequest.getBorrower().getName(),
            NotificationType.OVERDUE);
      }
    }
  }

  private void assertOwner(BorrowRequest borrowRequest, User currentUser) {
    if (!borrowRequest.getTool().getOwner().getId().equals(currentUser.getId())) {
      throw new ForbiddenException("Only the tool owner can perform this action");
    }
  }

  private void assertParticipant(BorrowRequest borrowRequest, User currentUser) {
    Long borrowerId = borrowRequest.getBorrower().getId();
    Long ownerId = borrowRequest.getTool().getOwner().getId();
    if (!borrowerId.equals(currentUser.getId()) && !ownerId.equals(currentUser.getId())) {
      throw new ForbiddenException("You are not part of this borrow request");
    }
  }

  public BorrowRequestResponse toResponse(BorrowRequest borrowRequest) {
    return new BorrowRequestResponse(
        borrowRequest.getId(),
        borrowRequest.getTool().getId(),
        borrowRequest.getTool().getName(),
        borrowRequest.getTool().getOwner().getId(),
        borrowRequest.getBorrower().getId(),
        borrowRequest.getBorrower().getName(),
        borrowRequest.getRequestedStartDate(),
        borrowRequest.getRequestedEndDate(),
        borrowRequest.getStatus(),
        borrowRequest.getCreatedAt());
  }
}
