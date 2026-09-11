package com.example.app.service;

import com.example.app.dto.NotificationResponse;
import com.example.app.entity.Notification;
import com.example.app.entity.NotificationType;
import com.example.app.entity.User;
import com.example.app.exception.ForbiddenException;
import com.example.app.exception.ResourceNotFoundException;
import com.example.app.repository.NotificationRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class NotificationService {

  private final NotificationRepository notificationRepository;

  public NotificationService(NotificationRepository notificationRepository) {
    this.notificationRepository = notificationRepository;
  }

  @Transactional
  public void notify(User user, String message, NotificationType type) {
    Notification notification = new Notification();
    notification.setUser(user);
    notification.setMessage(message);
    notification.setType(type);
    notification.setRead(false);
    notificationRepository.save(notification);
  }

  @Transactional(readOnly = true)
  public Page<NotificationResponse> getMyNotifications(Long userId, Pageable pageable) {
    return notificationRepository.findByUserId(userId, pageable).map(this::toResponse);
  }

  @Transactional
  public NotificationResponse markRead(Long id, User currentUser) {
    Notification notification =
        notificationRepository
            .findById(id)
            .orElseThrow(
                () -> new ResourceNotFoundException("Notification not found with id: " + id));
    if (!notification.getUser().getId().equals(currentUser.getId())) {
      throw new ForbiddenException("This notification does not belong to you");
    }
    notification.setRead(true);
    Notification saved = notificationRepository.save(notification);
    return toResponse(saved);
  }

  public NotificationResponse toResponse(Notification notification) {
    return new NotificationResponse(
        notification.getId(),
        notification.getMessage(),
        notification.getType(),
        notification.isRead(),
        notification.getCreatedAt());
  }
}
