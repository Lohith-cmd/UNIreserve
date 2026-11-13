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
  Analytics, 
  Holiday,
   MaintenanceWindow,
    RankedItem
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

export interface RawHoliday {
  holiday_id: number;
  holiday_date: string;
  description: string | null;
}

export interface RawMaintenance {
  schedule_id: number;
  facility_id: number;
  facility_name: string | null;
  start_date: string;
  end_date: string;
  start_time: string;
  end_time: string;
  description: string | null;
}

export interface RawWeekly {
  facility_id: number;
  facility_name: string;
  week_start: string;
  total_requests: number;
  confirmed: number;
  pending: number;
  rejected: number;
  cancelled: number;
  booked_hours: number;
}

type Loose = Record<string, unknown>;

export interface RawAnalytics {
  summary?: RawWeekly[];
  weekly_summary?: RawWeekly[];
  status_counts?: Record<string, number>;
  status_breakdown?: Record<string, number>;
  role_breakdown?: Record<string, number>;
  top_facilities?: Loose[];
  peak_hours?: Loose[];
}

export function toHoliday(r: RawHoliday): Holiday {
  return { holidayId: r.holiday_id, holidayDate: r.holiday_date, description: r.description };
}

export function toMaintenance(r: RawMaintenance): MaintenanceWindow {
  return {
    scheduleId: r.schedule_id,
    facilityId: r.facility_id,
    facilityName: r.facility_name ?? `Facility ${r.facility_id}`,
    startDate: r.start_date,
    endDate: r.end_date,
    startTime: hhmm(r.start_time),
    endTime: hhmm(r.end_time),
    description: r.description,
  };
}

// The backend types these dicts loosely, so we try several likely key names.
const NAME_KEYS = ["facility_name", "name", "facility"];
const HOUR_KEYS = ["hour", "start_hour", "hour_of_day", "time_slot", "slot", "start_time"];
const COUNT_KEYS = [
  "total_bookings", "booking_count", "bookings", "total_requests",
  "request_count", "count", "total",
];

function pick(obj: Loose, keys: string[]): unknown {
  for (const k of keys) {
    if (obj[k] !== undefined && obj[k] !== null) return obj[k];
  }
  return undefined;
}

function toRanked(items: Loose[], labelKeys: string[], asHour = false): RankedItem[] {
  return items.map((item) => {
    const raw = pick(item, labelKeys);
    let label = raw === undefined ? "?" : String(raw);
    if (asHour && typeof raw === "number") label = `${String(raw).padStart(2, "0")}:00`;
    if (asHour && typeof raw === "string" && raw.includes(":")) label = raw.slice(0, 5);
    return { label, count: Number(pick(item, COUNT_KEYS) ?? 0) };
  });
}

export function toAnalytics(r: RawAnalytics): Analytics {
  return {
    statusCounts: r.status_counts ?? r.status_breakdown ?? {},
    roleBreakdown: r.role_breakdown ?? {},
    topFacilities: toRanked(r.top_facilities ?? [], NAME_KEYS),
    peakHours: toRanked(r.peak_hours ?? [], HOUR_KEYS, true),
    weekly: (r.weekly_summary ?? r.summary ?? []).map((w) => ({
      facilityId: w.facility_id,
      facilityName: w.facility_name,
      weekStart: w.week_start,
      totalRequests: Number(w.total_requests),
      confirmed: Number(w.confirmed),
      pending: Number(w.pending),
      rejected: Number(w.rejected),
      cancelled: Number(w.cancelled),
      bookedHours: Number(w.booked_hours),
    })),
  };
}