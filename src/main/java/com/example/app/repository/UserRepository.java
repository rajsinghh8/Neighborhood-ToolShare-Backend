package com.example.app.repository;

import com.example.app.entity.User;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserRepository extends JpaRepository<User, Long> {

  Optional<User> findByEmail(String email);

  Optional<User> findByApiKey(String apiKey);

  boolean existsByEmail(String email);
}
