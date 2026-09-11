package com.example.app.controller;

import com.example.app.dto.BorrowRequestCreateRequest;
import com.example.app.dto.BorrowRequestResponse;
import com.example.app.entity.User;
import com.example.app.service.BorrowRequestService;
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
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/borrow-requests")
@Tag(
    name = "Borrow Requests",
    description = "Borrow request lifecycle: request, approve, reject, activate, return")
public class BorrowRequestController {

  private final BorrowRequestService borrowRequestService;

  private final UserService userService;

  public BorrowRequestController(
      BorrowRequestService borrowRequestService, UserService userService) {
    this.borrowRequestService = borrowRequestService;
    this.userService = userService;
  }

  @PostMapping
  @Operation(summary = "Request to borrow a tool")
  public ResponseEntity<BorrowRequestResponse> create(
      Authentication authentication, @Valid @RequestBody BorrowRequestCreateRequest request) {
    User borrower = userService.getByEmail(authentication.getName());
    return ResponseEntity.status(HttpStatus.CREATED)
        .body(borrowRequestService.create(borrower, request));
  }

  @GetMapping
  @Operation(
      summary =
          "List borrow requests belonging to the current user, either as borrower or as tool owner")
  public ResponseEntity<Page<BorrowRequestResponse>> getMine(
      Authentication authentication,
      @RequestParam(defaultValue = "borrower") String role,
      @PageableDefault(size = 20) Pageable pageable) {
    User user = userService.getByEmail(authentication.getName());
    if ("owner".equalsIgnoreCase(role)) {
      return ResponseEntity.ok(borrowRequestService.getMyRequestsAsOwner(user.getId(), pageable));
    }
    return ResponseEntity.ok(borrowRequestService.getMyRequestsAsBorrower(user.getId(), pageable));
  }

  @GetMapping("/{id}")
  @Operation(summary = "Get a single borrow request by id")
  public ResponseEntity<BorrowRequestResponse> getById(
      Authentication authentication, @PathVariable Long id) {
    User user = userService.getByEmail(authentication.getName());
    return ResponseEntity.ok(borrowRequestService.getById(id, user));
  }

  @PutMapping("/{id}/approve")
  @Operation(summary = "Owner approves a pending borrow request, creating a reservation")
  public ResponseEntity<BorrowRequestResponse> approve(
      Authentication authentication, @PathVariable Long id) {
    User owner = userService.getByEmail(authentication.getName());
    return ResponseEntity.ok(borrowRequestService.approve(id, owner));
  }

  @PutMapping("/{id}/reject")
  @Operation(summary = "Owner rejects a pending borrow request")
  public ResponseEntity<BorrowRequestResponse> reject(
      Authentication authentication, @PathVariable Long id) {
    User owner = userService.getByEmail(authentication.getName());
    return ResponseEntity.ok(borrowRequestService.reject(id, owner));
  }

  @PutMapping("/{id}/activate")
  @Operation(summary = "Mark an approved borrow request as active (tool picked up)")
  public ResponseEntity<BorrowRequestResponse> activate(
      Authentication authentication, @PathVariable Long id) {
    User user = userService.getByEmail(authentication.getName());
    return ResponseEntity.ok(borrowRequestService.activate(id, user));
  }

  @PutMapping("/{id}/return")
  @Operation(summary = "Mark an active or overdue borrow request as returned")
  public ResponseEntity<BorrowRequestResponse> markReturned(
      Authentication authentication, @PathVariable Long id) {
    User user = userService.getByEmail(authentication.getName());
    return ResponseEntity.ok(borrowRequestService.markReturned(id, user));
  }
}
