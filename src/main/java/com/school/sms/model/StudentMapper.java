package com.school.sms.model;

import com.school.sms.dto.Dtos.StudentRequest;
import com.school.sms.dto.Dtos.StudentResponse;

/** Converts between the {@link Student} entity and its wire DTOs. */
public final class StudentMapper {

    private StudentMapper() {
    }

    public static Student toEntity(StudentRequest request) {
        Student student = new Student();
        copyInto(student, request);
        return student;
    }

    /** Full replace of every mutable field. */
    public static void copyInto(Student student, StudentRequest request) {
        student.setFirstName(request.firstName());
        student.setLastName(request.lastName());
        student.setDateOfBirth(request.dateOfBirth());
        student.setGradeLevel(request.gradeLevel());
        student.setSection(request.section());
        student.setGuardianName(request.guardianName());
        student.setGuardianPhone(request.guardianPhone());
        student.setActive(request.active());
    }

    public static StudentResponse toResponse(Student student) {
        return new StudentResponse(
                student.getId(),
                student.getFirstName(),
                student.getLastName(),
                student.getDateOfBirth(),
                student.getGradeLevel(),
                student.getSection(),
                student.getGuardianName(),
                student.getGuardianPhone(),
                student.isActive());
    }
}
