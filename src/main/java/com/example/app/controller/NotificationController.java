package com.example.app.controller;

import com.example.app.dto.NotificationResponse;
import com.example.app.entity.User;
import com.example.app.service.NotificationService;
import com.example.app.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/notifications")
@Tag(
    name = "Notifications",
    description = "Alerts about requests, approvals, due dates and overdue tools")
public class NotificationController {

  private final NotificationService notificationService;

  private final UserService userService;

  public NotificationController(NotificationService notificationService, UserService userService) {
    this.notificationService = notificationService;
    this.userService = userService;
  }

  @GetMapping
  @Operation(summary = "List notifications for the current user (paginated)")
  public ResponseEntity<Page<NotificationResponse>> getMine(
      Authentication authentication, @PageableDefault(size = 20) Pageable pageable) {
    User user = userService.getByEmail(authentication.getName());
    return ResponseEntity.ok(notificationService.getMyNotifications(user.getId(), pageable));
  }

  @PutMapping("/{id}/read")
  @Operation(summary = "Mark a notification as read")
  public ResponseEntity<NotificationResponse> markRead(
      Authentication authentication, @PathVariable Long id) {
    User user = userService.getByEmail(authentication.getName());
    return ResponseEntity.ok(notificationService.markRead(id, user));
  }
}
