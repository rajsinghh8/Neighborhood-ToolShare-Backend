package com.example.app.dto;

public class ReservationUpdateRequest {

  private String pickupNotes;

  private String returnNotes;

  public String getPickupNotes() {
    return pickupNotes;
  }

  public void setPickupNotes(String pickupNotes) {
    this.pickupNotes = pickupNotes;
  }

  public String getReturnNotes() {
    return returnNotes;
  }

  public void setReturnNotes(String returnNotes) {
    this.returnNotes = returnNotes;
  }
}
