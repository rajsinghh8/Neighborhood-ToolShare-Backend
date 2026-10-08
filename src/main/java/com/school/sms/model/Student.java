package com.school.sms.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Table;
import java.time.LocalDate;

/** A pupil enrolled at the school. */
@Entity
@Table(name = "STUDENT", indexes = @Index(name = "IDX_STUDENT_GRADE_LEVEL", columnList = "GRADE_LEVEL"))
public class Student {

    private static final int NAME_LENGTH = 100;
    private static final int SECTION_LENGTH = 20;
    private static final int GUARDIAN_NAME_LENGTH = 200;
    private static final int GUARDIAN_PHONE_LENGTH = 30;

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "FIRST_NAME", nullable = false, length = NAME_LENGTH)
    private String firstName;

    @Column(name = "LAST_NAME", nullable = false, length = NAME_LENGTH)
    private String lastName;

    @Column(name = "DATE_OF_BIRTH", nullable = false)
    private LocalDate dateOfBirth;

    @Column(name = "GRADE_LEVEL", nullable = false)
    private Integer gradeLevel;

    @Column(name = "SECTION", length = SECTION_LENGTH)
    private String section;

    @Column(name = "GUARDIAN_NAME", length = GUARDIAN_NAME_LENGTH)
    private String guardianName;

    @Column(name = "GUARDIAN_PHONE", length = GUARDIAN_PHONE_LENGTH)
    private String guardianPhone;

    @Column(name = "IS_ACTIVE", nullable = false)
    private boolean active;

    protected Student() {
        // required by JPA
    }

    public Long getId() {
        return id;
    }

    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }

    public LocalDate getDateOfBirth() {
        return dateOfBirth;
    }

    public void setDateOfBirth(LocalDate dateOfBirth) {
        this.dateOfBirth = dateOfBirth;
    }

    public Integer getGradeLevel() {
        return gradeLevel;
    }

    public void setGradeLevel(Integer gradeLevel) {
        this.gradeLevel = gradeLevel;
    }

    public String getSection() {
        return section;
    }

    public void setSection(String section) {
        this.section = section;
    }

    public String getGuardianName() {
        return guardianName;
    }

    public void setGuardianName(String guardianName) {
        this.guardianName = guardianName;
    }

    public String getGuardianPhone() {
        return guardianPhone;
    }

    public void setGuardianPhone(String guardianPhone) {
        this.guardianPhone = guardianPhone;
    }

    public boolean isActive() {
        return active;
    }

    public void setActive(boolean active) {
        this.active = active;
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        }
        if (other == null || getClass() != other.getClass()) {
            return false;
        }
        Student that = (Student) other;
        return id != null && id.equals(that.id);
    }

    @Override
    public int hashCode() {
        return getClass().hashCode();
    }
}
