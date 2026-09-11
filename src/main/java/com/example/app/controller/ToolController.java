package com.example.app.controller;

import com.example.app.dto.ToolRequest;
import com.example.app.dto.ToolResponse;
import com.example.app.entity.User;
import com.example.app.service.ToolService;
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
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/tools")
@Tag(name = "Tools", description = "Tool listing management and search")
public class ToolController {

  private final ToolService toolService;

  private final UserService userService;

  public ToolController(ToolService toolService, UserService userService) {
    this.toolService = toolService;
    this.userService = userService;
  }

  @PostMapping
  @Operation(summary = "Add a new tool listing owned by the current user")
  public ResponseEntity<ToolResponse> createTool(
      Authentication authentication, @Valid @RequestBody ToolRequest request) {
    User owner = userService.getByEmail(authentication.getName());
    return ResponseEntity.status(HttpStatus.CREATED).body(toolService.createTool(owner, request));
  }

  @GetMapping
  @Operation(summary = "Search/browse tools by category, neighborhood and availability (paginated)")
  public ResponseEntity<Page<ToolResponse>> search(
      @RequestParam(required = false) String category,
      @RequestParam(required = false) String neighborhood,
      @RequestParam(required = false) Boolean available,
      @PageableDefault(size = 20) Pageable pageable) {
    return ResponseEntity.ok(toolService.search(category, neighborhood, available, pageable));
  }

  @GetMapping("/mine")
  @Operation(summary = "List tools owned by the current user (paginated)")
  public ResponseEntity<Page<ToolResponse>> getMyTools(
      Authentication authentication, @PageableDefault(size = 20) Pageable pageable) {
    User owner = userService.getByEmail(authentication.getName());
    return ResponseEntity.ok(toolService.getMyTools(owner.getId(), pageable));
  }

  @GetMapping("/{id}")
  @Operation(summary = "Get a single tool by id")
  public ResponseEntity<ToolResponse> getById(@PathVariable Long id) {
    return ResponseEntity.ok(toolService.getById(id));
  }

  @PutMapping("/{id}")
  @Operation(summary = "Edit a tool owned by the current user")
  public ResponseEntity<ToolResponse> updateTool(
      Authentication authentication,
      @PathVariable Long id,
      @Valid @RequestBody ToolRequest request) {
    User owner = userService.getByEmail(authentication.getName());
    return ResponseEntity.ok(toolService.updateTool(id, owner, request));
  }

  @PutMapping("/{id}/availability")
  @Operation(summary = "Mark a tool as available or unavailable")
  public ResponseEntity<ToolResponse> setAvailability(
      Authentication authentication, @PathVariable Long id, @RequestParam boolean available) {
    User owner = userService.getByEmail(authentication.getName());
    return ResponseEntity.ok(toolService.setAvailability(id, owner, available));
  }

  @DeleteMapping("/{id}")
  @Operation(summary = "Remove a tool owned by the current user")
  public ResponseEntity<Void> deleteTool(Authentication authentication, @PathVariable Long id) {
    User owner = userService.getByEmail(authentication.getName());
    toolService.deleteTool(id, owner);
    return ResponseEntity.noContent().build();
  }
}
