package com.example.app.service;

import com.example.app.dto.UserResponse;
import com.example.app.dto.UserUpdateRequest;
import com.example.app.entity.User;
import com.example.app.exception.ResourceNotFoundException;
import com.example.app.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class UserService {

  private final UserRepository userRepository;

  public UserService(UserRepository userRepository) {
    this.userRepository = userRepository;
  }

  public User getByEmail(String email) {
    return userRepository
        .findByEmail(email)
        .orElseThrow(() -> new ResourceNotFoundException("User not found with email: " + email));
  }

  public User getById(Long id) {
    return userRepository
        .findById(id)
        .orElseThrow(() -> new ResourceNotFoundException("User not found with id: " + id));
  }

  public UserResponse getCurrentUser(String email) {
    return toResponse(getByEmail(email));
  }

  @Transactional
  public UserResponse updateCurrentUser(String email, UserUpdateRequest request) {
    User user = getByEmail(email);
    if (request.getName() != null && !request.getName().isBlank()) {
      user.setName(request.getName());
    }
    if (request.getNeighborhood() != null) {
      user.setNeighborhood(request.getNeighborhood());
    }
    if (request.getPhone() != null) {
      user.setPhone(request.getPhone());
    }
    User saved = userRepository.save(user);
    return toResponse(saved);
  }

  public UserResponse toResponse(User user) {
    return new UserResponse(
        user.getId(),
        user.getName(),
        user.getEmail(),
        user.getNeighborhood(),
        user.getPhone(),
        user.getApiKey(),
        user.getCreatedAt());
  }
}
