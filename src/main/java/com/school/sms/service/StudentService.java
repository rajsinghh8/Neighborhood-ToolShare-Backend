package com.school.sms.service;

import com.school.sms.dto.Dtos.PageResponse;
import com.school.sms.dto.Dtos.StudentCountResponse;
import com.school.sms.dto.Dtos.StudentRequest;
import com.school.sms.dto.Dtos.StudentResponse;
import com.school.sms.exception.NotFoundException;
import com.school.sms.kafka.StudentEventPublisher;
import com.school.sms.kafka.StudentEventType;
import com.school.sms.model.Student;
import com.school.sms.model.StudentMapper;
import com.school.sms.repository.OffsetBasedPageRequest;
import com.school.sms.repository.StudentRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Business logic for student CRUD; every write also records a domain event in the same transaction. */
@Service
public class StudentService {

    private static final Logger log = LoggerFactory.getLogger(StudentService.class);
    private static final Sort DEFAULT_SORT = Sort.by(Sort.Direction.ASC, "id");

    private final StudentRepository studentRepository;
    private final StudentEventPublisher studentEventPublisher;

    public StudentService(StudentRepository studentRepository, StudentEventPublisher studentEventPublisher) {
        this.studentRepository = studentRepository;
        this.studentEventPublisher = studentEventPublisher;
    }

    @Transactional(readOnly = true)
    public PageResponse<StudentResponse> list(Integer gradeLevel, int offset, int limit) {
        Pageable pageable = new OffsetBasedPageRequest(offset, limit, DEFAULT_SORT);
        Page<Student> page = gradeLevel == null
                ? studentRepository.findAll(pageable)
                : studentRepository.findByGradeLevel(gradeLevel, pageable);
        log.debug("Students listed [offset={}, limit={}, returned={}, total={}]",
                offset, limit, page.getNumberOfElements(), page.getTotalElements());
        return new PageResponse<>(
                page.getContent().stream().map(StudentMapper::toResponse).toList(),
                offset,
                limit,
                page.getTotalElements());
    }

    @Transactional(readOnly = true)
    public StudentCountResponse getStudentCount() {
        long count = studentRepository.count();
        log.debug("Student count requested: total={}", count);
        return new StudentCountResponse(count);
    }

    @Transactional(readOnly = true)
    public StudentResponse get(Long id) {
        log.debug("Student requested [id={}]", id);
        return StudentMapper.toResponse(findOrThrow(id));
    }

    @Transactional
    public StudentResponse create(StudentRequest request) {
        Student saved = studentRepository.save(StudentMapper.toEntity(request));
        studentEventPublisher.publish(StudentEventType.CREATED, saved.getId());
        log.info("Student created [id={}]", saved.getId());
        return StudentMapper.toResponse(saved);
    }

    @Transactional
    public StudentResponse update(Long id, StudentRequest request) {
        Student student = findOrThrow(id);
        StudentMapper.copyInto(student, request);
        Student saved = studentRepository.save(student);
        studentEventPublisher.publish(StudentEventType.UPDATED, saved.getId());
        log.info("Student updated [id={}]", saved.getId());
        return StudentMapper.toResponse(saved);
    }

    @Transactional
    public void delete(Long id) {
        Student student = findOrThrow(id);
        studentRepository.delete(student);
        studentEventPublisher.publish(StudentEventType.DELETED, id);
        log.info("Student deleted [id={}]", id);
    }

    private Student findOrThrow(Long id) {
        return studentRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("Student not found: id=" + id));
    }
}
