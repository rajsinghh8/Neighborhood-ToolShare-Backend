package com.example.app.repository;

import com.example.app.entity.Tool;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ToolRepository extends JpaRepository<Tool, Long> {

  Page<Tool> findByOwnerId(Long ownerId, Pageable pageable);

  @Query(
      "select t from Tool t where (:category is null or lower(t.category) = lower(cast(:category as"
          + " string))) and (:neighborhood is null or lower(t.owner.neighborhood) ="
          + " lower(cast(:neighborhood as string))) and (:available is null or t.available ="
          + " :available)")
  Page<Tool> search(
      @Param("category") String category,
      @Param("neighborhood") String neighborhood,
      @Param("available") Boolean available,
      Pageable pageable);
}
