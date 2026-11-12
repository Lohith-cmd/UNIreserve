import type {
  Booking,
  BookingStatus,
  Facility,
  FacilityStatus,
  FacilityType,
  PendingBooking,
  Role,
  StatusLogEntry,
  User,
} from "../types";

const hhmm = (t: string) => t.slice(0, 5);

export interface RawUser {
  user_id: number;
  name: string;
  email: string;
  role: string;
}

export interface RawLog {
  log_id: number;
  booking_id: number;
  old_status: string | null;
  new_status: string;
  changed_by_user_id: number | null;
  changed_by_name: string | null;
  changed_at: string;
}

export interface RawFacility {
  facility_id: number;
  name: string;
  location: string | null;
  facility_type: string;
  status: string;
  pending_requests?: number;
}

export interface RawBooking {
  booking_id: number;
  user_id: number;
  facility_id: number;
  facility_name: string | null;
  booking_date: string;
  start_time: string;
  end_time: string;
  status: string;
  purpose: string | null;
  status_logs?: RawLog[];
  logs?: RawLog[];
}

export interface RawPending extends RawBooking {
  user_name: string;
  user_role: string;
}

export function toUser(r: RawUser): User {
  return { userId: r.user_id, name: r.name, email: r.email, role: r.role as Role };
}

export function toLog(r: RawLog): StatusLogEntry {
  return {
    logId: r.log_id,
    bookingId: r.booking_id,
    oldStatus: r.old_status as BookingStatus | null,
    newStatus: r.new_status as BookingStatus,
    changedAt: r.changed_at,
    changedBy: r.changed_by_user_id,
    changedByName: r.changed_by_name,
  };
}

export function toFacility(r: RawFacility): Facility {
  return {
    facilityId: r.facility_id,
    name: r.name,
    type: r.facility_type as FacilityType,
    status: r.status as FacilityStatus,
    location: r.location,
    pendingRequests: r.pending_requests,
  };
}

export function toBooking(r: RawBooking): Booking {
  return {
    bookingId: r.booking_id,
    userId: r.user_id,
    facilityId: r.facility_id,
    facilityName: r.facility_name ?? `Facility ${r.facility_id}`,
    bookingDate: r.booking_date,
    startTime: hhmm(r.start_time),
    endTime: hhmm(r.end_time),
    status: r.status as BookingStatus,
    purpose: r.purpose,
  };
}

export function toPending(r: RawPending): PendingBooking {
  return { ...toBooking(r), userName: r.user_name, userRole: r.user_role as Role };
}