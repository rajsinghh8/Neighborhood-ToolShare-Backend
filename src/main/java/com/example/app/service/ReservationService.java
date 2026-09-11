package com.example.app.service;

import com.example.app.dto.ReservationResponse;
import com.example.app.dto.ReservationUpdateRequest;
import com.example.app.entity.BorrowRequest;
import com.example.app.entity.Reservation;
import com.example.app.entity.User;
import com.example.app.exception.ForbiddenException;
import com.example.app.exception.ResourceNotFoundException;
import com.example.app.repository.ReservationRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ReservationService {

  private final ReservationRepository reservationRepository;

  public ReservationService(ReservationRepository reservationRepository) {
    this.reservationRepository = reservationRepository;
  }

  @Transactional
  public Reservation createReservation(BorrowRequest borrowRequest) {
    Reservation reservation = new Reservation();
    reservation.setBorrowRequest(borrowRequest);
    reservation.setStartDate(borrowRequest.getRequestedStartDate());
    reservation.setEndDate(borrowRequest.getRequestedEndDate());
    return reservationRepository.save(reservation);
  }

  @Transactional(readOnly = true)
  public Page<ReservationResponse> getMyReservationsAsBorrower(Long borrowerId, Pageable pageable) {
    return reservationRepository
        .findByBorrowRequest_Borrower_Id(borrowerId, pageable)
        .map(this::toResponse);
  }

  @Transactional(readOnly = true)
  public Page<ReservationResponse> getMyReservationsAsOwner(Long ownerId, Pageable pageable) {
    return reservationRepository
        .findByBorrowRequest_Tool_Owner_Id(ownerId, pageable)
        .map(this::toResponse);
  }

  @Transactional(readOnly = true)
  public Reservation getEntityById(Long id) {
    return reservationRepository
        .findById(id)
        .orElseThrow(() -> new ResourceNotFoundException("Reservation not found with id: " + id));
  }

  @Transactional(readOnly = true)
  public ReservationResponse getById(Long id, User currentUser) {
    Reservation reservation = getEntityById(id);
    assertParticipant(reservation, currentUser);
    return toResponse(reservation);
  }

  @Transactional
  public ReservationResponse update(Long id, User currentUser, ReservationUpdateRequest request) {
    Reservation reservation = getEntityById(id);
    assertParticipant(reservation, currentUser);
    if (request.getPickupNotes() != null) {
      reservation.setPickupNotes(request.getPickupNotes());
    }
    if (request.getReturnNotes() != null) {
      reservation.setReturnNotes(request.getReturnNotes());
    }
    Reservation saved = reservationRepository.save(reservation);
    return toResponse(saved);
  }

  private void assertParticipant(Reservation reservation, User currentUser) {
    Long borrowerId = reservation.getBorrowRequest().getBorrower().getId();
    Long ownerId = reservation.getBorrowRequest().getTool().getOwner().getId();
    if (!borrowerId.equals(currentUser.getId()) && !ownerId.equals(currentUser.getId())) {
      throw new ForbiddenException("You are not part of this reservation");
    }
  }

  public ReservationResponse toResponse(Reservation reservation) {
    BorrowRequest br = reservation.getBorrowRequest();
    return new ReservationResponse(
        reservation.getId(),
        br.getId(),
        br.getTool().getId(),
        br.getTool().getName(),
        br.getBorrower().getId(),
        reservation.getStartDate(),
        reservation.getEndDate(),
        reservation.getPickupNotes(),
        reservation.getReturnNotes(),
        reservation.getCreatedAt());
  }
}
