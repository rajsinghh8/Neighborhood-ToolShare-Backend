package com.example.app.controller;

import com.example.app.dto.UserResponse;
import com.example.app.dto.UserUpdateRequest;
import com.example.app.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/users")
@Tag(name = "Users", description = "Current user's profile management")
public class UserController {

  private final UserService userService;

  public UserController(UserService userService) {
    this.userService = userService;
  }

  @GetMapping("/me")
  @Operation(summary = "Get the currently authenticated user's profile, including the API key")
  public ResponseEntity<UserResponse> getMe(Authentication authentication) {
    return ResponseEntity.ok(userService.getCurrentUser(authentication.getName()));
  }

  @PutMapping("/me")
  @Operation(summary = "Update the currently authenticated user's profile")
  public ResponseEntity<UserResponse> updateMe(
      Authentication authentication, @Valid @RequestBody UserUpdateRequest request) {
    return ResponseEntity.ok(userService.updateCurrentUser(authentication.getName(), request));
  }
}
