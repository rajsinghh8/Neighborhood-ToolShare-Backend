package com.school.sms.controller;

import com.school.sms.dto.Dtos;
import com.school.sms.dto.Dtos.PageResponse;
import com.school.sms.dto.Dtos.StudentRequest;
import com.school.sms.dto.Dtos.StudentResponse;
import com.school.sms.service.StudentService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import java.net.URI;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.util.UriComponentsBuilder;

@RestController
@RequestMapping(StudentController.BASE_PATH)
@Validated
@Tag(name = "Students")
@SecurityRequirement(name = "bearerAuth")
public class StudentController {

    static final String BASE_PATH = "/api/v1/students";

    private static final String DEFAULT_OFFSET = "0";
    private static final String DEFAULT_LIMIT = "20";
    private static final int MAX_LIMIT = 100;
    private static final String READ_ROLES = "hasAnyRole('ADMIN','TEACHER')";
    private static final String WRITE_ROLE = "hasRole('ADMIN')";

    private final StudentService studentService;

    public StudentController(StudentService studentService) {
        this.studentService = studentService;
    }

    @GetMapping
    @PreAuthorize(READ_ROLES)
    @Operation(summary = "List students with offset/limit pagination and optional grade filter")
    public PageResponse<StudentResponse> list(
            @RequestParam(name = "grade", required = false) @Min(Dtos.MIN_GRADE) @Max(Dtos.MAX_GRADE) Integer grade,
            @RequestParam(defaultValue = DEFAULT_OFFSET) @Min(0) int offset,
            @RequestParam(defaultValue = DEFAULT_LIMIT) @Min(1) @Max(MAX_LIMIT) int limit) {
        return studentService.list(grade, offset, limit);
    }

    @GetMapping("/{id}")
    @PreAuthorize(READ_ROLES)
    @Operation(summary = "Get a student by id")
    public StudentResponse get(@PathVariable Long id) {
        return studentService.get(id);
    }

    @PostMapping
    @PreAuthorize(WRITE_ROLE)
    @Operation(summary = "Create a student (admin only)")
    public ResponseEntity<StudentResponse> create(@Valid @RequestBody StudentRequest request) {
        StudentResponse created = studentService.create(request);
        URI location = UriComponentsBuilder.fromPath(BASE_PATH + "/{id}").buildAndExpand(created.id()).toUri();
        return ResponseEntity.created(location).body(created);
    }

    @PutMapping("/{id}")
    @PreAuthorize(WRITE_ROLE)
    @Operation(summary = "Replace a student (admin only)")
    public StudentResponse update(@PathVariable Long id, @Valid @RequestBody StudentRequest request) {
        return studentService.update(id, request);
    }

    @DeleteMapping("/{id}")
    @PreAuthorize(WRITE_ROLE)
    @Operation(summary = "Delete a student (admin only)")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        studentService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
