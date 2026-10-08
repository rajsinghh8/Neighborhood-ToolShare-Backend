package com.school.sms.kafka;

import java.util.List;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface OutboxEventRepository extends JpaRepository<OutboxEvent, Long> {

    /** Oldest unpublished events first, so delivery order matches write order. */
    List<OutboxEvent> findByPublishedAtIsNullOrderByIdAsc(Pageable pageable);

    long countByPublishedAtIsNull();
}
