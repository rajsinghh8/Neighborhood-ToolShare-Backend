package com.example.app.controller;

import com.example.app.dto.ReservationResponse;
import com.example.app.dto.ReservationUpdateRequest;
import com.example.app.entity.User;
import com.example.app.service.ReservationService;
import com.example.app.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/reservations")
@Tag(name = "Reservations", description = "Confirmed borrow periods with pickup/return notes")
public class ReservationController {

  private final ReservationService reservationService;

  private final UserService userService;

  public ReservationController(ReservationService reservationService, UserService userService) {
    this.reservationService = reservationService;
    this.userService = userService;
  }

  @GetMapping
  @Operation(
      summary =
          "List reservations belonging to the current user, either as borrower or as tool owner")
  public ResponseEntity<Page<ReservationResponse>> getMine(
      Authentication authentication,
      @RequestParam(defaultValue = "borrower") String role,
      @PageableDefault(size = 20) Pageable pageable) {
    User user = userService.getByEmail(authentication.getName());
    if ("owner".equalsIgnoreCase(role)) {
      return ResponseEntity.ok(reservationService.getMyReservationsAsOwner(user.getId(), pageable));
    }
    return ResponseEntity.ok(
        reservationService.getMyReservationsAsBorrower(user.getId(), pageable));
  }

  @GetMapping("/{id}")
  @Operation(summary = "Get a single reservation by id")
  public ResponseEntity<ReservationResponse> getById(
      Authentication authentication, @PathVariable Long id) {
    User user = userService.getByEmail(authentication.getName());
    return ResponseEntity.ok(reservationService.getById(id, user));
  }

  @PutMapping("/{id}")
  @Operation(summary = "Update pickup/return notes on a reservation")
  public ResponseEntity<ReservationResponse> update(
      Authentication authentication,
      @PathVariable Long id,
      @Valid @RequestBody ReservationUpdateRequest request) {
    User user = userService.getByEmail(authentication.getName());
    return ResponseEntity.ok(reservationService.update(id, user, request));
  }
}
