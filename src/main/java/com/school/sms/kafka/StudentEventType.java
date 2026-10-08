package com.school.sms.kafka;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import java.util.Arrays;

/** Kind of change a student event describes; serialised in lower case ("created", ...). */
public enum StudentEventType {
    CREATED("created"),
    UPDATED("updated"),
    DELETED("deleted");

    private final String wireValue;

    StudentEventType(String wireValue) {
        this.wireValue = wireValue;
    }

    @JsonValue
    public String wireValue() {
        return wireValue;
    }

    @JsonCreator
    public static StudentEventType fromWireValue(String value) {
        return Arrays.stream(values())
                .filter(type -> type.wireValue.equalsIgnoreCase(value))
                .findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Unknown student event type: " + value));
    }
}
