package com.example.app.controller;

import com.example.app.dto.FlaggedToolResponse;
import com.example.app.dto.OverdueUserResponse;
import com.example.app.service.AdminService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/admin")
@Tag(
    name = "Admin",
    description = "Basic admin views: repeatedly overdue users and flagged tool listings")
public class AdminController {

  private final AdminService adminService;

  public AdminController(AdminService adminService) {
    this.adminService = adminService;
  }

  @GetMapping("/overdue-users")
  @Operation(
      summary = "List users who have been overdue on a borrowed tool at least minCount times")
  public ResponseEntity<List<OverdueUserResponse>> getOverdueUsers(
      @RequestParam(defaultValue = "1") int minCount) {
    return ResponseEntity.ok(adminService.getRepeatedlyOverdueUsers(minCount));
  }

  @GetMapping("/flagged-tools")
  @Operation(
      summary = "List tool listings that have been involved in at least minCount overdue borrows")
  public ResponseEntity<List<FlaggedToolResponse>> getFlaggedTools(
      @RequestParam(defaultValue = "1") int minCount) {
    return ResponseEntity.ok(adminService.getFlaggedTools(minCount));
  }
}
