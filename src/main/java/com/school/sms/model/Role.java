package com.school.sms.model;

public enum Role {
    ADMIN,
    TEACHER;

    /** Spring Security authority name, e.g. {@code ROLE_ADMIN}. */
    public String authority() {
        return "ROLE_" + name();
    }
}
