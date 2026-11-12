export type Role = "Student" | "Faculty" | "Admin";

export type BookingStatus = "Pending" | "Confirmed" | "Rejected" | "Cancelled";

export type FacilityType = "Sports" | "Classroom";

export type FacilityStatus = "Active" | "Under Maintenance";

export interface User {
  userId: number;
  name: string;
  email: string;
  role: Role;
}

export interface Facility {
  facilityId: number;
  name: string;
  type: FacilityType;
  status: FacilityStatus;
}

export interface Booking {
  bookingId: number;
  userId: number;
  facilityId: number;
  facilityName: string;
  bookingDate: string; // "YYYY-MM-DD"
  startTime: string; // "HH:MM"
  endTime: string; // "HH:MM"
  status: BookingStatus;
}

export interface StatusLogEntry {
  logId: number;
  bookingId: number;
  oldStatus: BookingStatus | null;
  newStatus: BookingStatus;
  changedAt: string; // ISO timestamp
  changedBy: number | null;
}

export interface MaintenanceWindow {
  maintenanceId: number;
  facilityId: number;
  facilityName: string;
  startDate: string;
  endDate: string;
  reason: string;
}

export interface Holiday {
  holidayId: number;
  holidayDate: string;
  description: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}