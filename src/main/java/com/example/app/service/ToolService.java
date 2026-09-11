package com.example.app.service;

import com.example.app.dto.ToolRequest;
import com.example.app.dto.ToolResponse;
import com.example.app.entity.Tool;
import com.example.app.entity.User;
import com.example.app.exception.BadRequestException;
import com.example.app.exception.ForbiddenException;
import com.example.app.exception.ResourceNotFoundException;
import com.example.app.repository.ToolRepository;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ToolService {

  private final ToolRepository toolRepository;

  public ToolService(ToolRepository toolRepository) {
    this.toolRepository = toolRepository;
  }

  @Transactional
  public ToolResponse createTool(User owner, ToolRequest request) {
    Tool tool = new Tool();
    tool.setName(request.getName());
    tool.setCategory(request.getCategory());
    tool.setDescription(request.getDescription());
    tool.setCondition(request.getCondition());
    tool.setAvailable(request.getAvailable() == null || request.getAvailable());
    tool.setOwner(owner);
    Tool saved = toolRepository.save(tool);
    return toResponse(saved);
  }

  @Transactional(readOnly = true)
  public Page<ToolResponse> search(
      String category, String neighborhood, Boolean available, Pageable pageable) {
    return toolRepository.search(category, neighborhood, available, pageable).map(this::toResponse);
  }

  @Transactional(readOnly = true)
  public Page<ToolResponse> getMyTools(Long ownerId, Pageable pageable) {
    return toolRepository.findByOwnerId(ownerId, pageable).map(this::toResponse);
  }

  @Transactional(readOnly = true)
  public ToolResponse getById(Long id) {
    return toResponse(getEntityById(id));
  }

  public Tool getEntityById(Long id) {
    return toolRepository
        .findById(id)
        .orElseThrow(() -> new ResourceNotFoundException("Tool not found with id: " + id));
  }

  @Transactional
  public ToolResponse updateTool(Long id, User currentUser, ToolRequest request) {
    Tool tool = getEntityById(id);
    assertOwner(tool, currentUser);
    tool.setName(request.getName());
    tool.setCategory(request.getCategory());
    tool.setDescription(request.getDescription());
    tool.setCondition(request.getCondition());
    if (request.getAvailable() != null) {
      tool.setAvailable(request.getAvailable());
    }
    Tool saved = toolRepository.save(tool);
    return toResponse(saved);
  }

  @Transactional
  public void deleteTool(Long id, User currentUser) {
    Tool tool = getEntityById(id);
    assertOwner(tool, currentUser);
    try {
      toolRepository.delete(tool);
      toolRepository.flush();
    } catch (DataIntegrityViolationException ex) {
      throw new BadRequestException(
          "Cannot delete a tool that has existing borrow request history. "
              + "Mark it unavailable instead.");
    }
  }

  @Transactional
  public ToolResponse setAvailability(Long id, User currentUser, boolean available) {
    Tool tool = getEntityById(id);
    assertOwner(tool, currentUser);
    tool.setAvailable(available);
    Tool saved = toolRepository.save(tool);
    return toResponse(saved);
  }

  @Transactional
  public void updateAvailabilityDirect(Tool tool, boolean available) {
    tool.setAvailable(available);
    toolRepository.save(tool);
  }

  private void assertOwner(Tool tool, User currentUser) {
    if (!tool.getOwner().getId().equals(currentUser.getId())) {
      throw new ForbiddenException("You do not own this tool");
    }
  }

  public ToolResponse toResponse(Tool tool) {
    return new ToolResponse(
        tool.getId(),
        tool.getName(),
        tool.getCategory(),
        tool.getDescription(),
        tool.getCondition(),
        tool.isAvailable(),
        tool.getOwner().getId(),
        tool.getOwner().getName(),
        tool.getOwner().getNeighborhood(),
        tool.getCreatedAt());
  }
}
