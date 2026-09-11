package com.example.app.dto;

import com.example.app.entity.ToolCondition;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public class ToolRequest {

  @NotBlank(message = "name is required")
  private String name;

  @NotBlank(message = "category is required")
  private String category;

  private String description;

  @NotNull(message = "condition is required")
  private ToolCondition condition;

  private Boolean available;

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public String getCategory() {
    return category;
  }

  public void setCategory(String category) {
    this.category = category;
  }

  public String getDescription() {
    return description;
  }

  public void setDescription(String description) {
    this.description = description;
  }

  public ToolCondition getCondition() {
    return condition;
  }

  public void setCondition(ToolCondition condition) {
    this.condition = condition;
  }

  public Boolean getAvailable() {
    return available;
  }

  public void setAvailable(Boolean available) {
    this.available = available;
  }
}
