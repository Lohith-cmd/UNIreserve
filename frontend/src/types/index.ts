export type Role = "Student" | "Faculty" | "Admin";

export type BookingStatus = "Pending" | "Confirmed" | "Rejected" | "Cancelled" | "Completed";

export type FacilityType = "Sports" | "Classroom" | "Other";

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
  location?: string | null;
  pendingRequests?: number;
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
  purpose?: string | null;
}

export interface StatusLogEntry {
  logId: number;
  bookingId: number;
  oldStatus: BookingStatus | null;
  newStatus: BookingStatus;
  changedAt: string; // ISO timestamp
  changedBy: number | null;
  changedByName?: string | null;
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

export interface PendingBooking extends Booking {
  userName: string;
  userRole: Role;
}

export interface ConfirmResult {
  autoRejected?: number;
  message?: string;
}