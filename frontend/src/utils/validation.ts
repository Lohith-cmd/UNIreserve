import type { Facility, Role } from "../types";

export function toMinutes(t: string): number {
  const [h, m] = t.split(":").map(Number);
  return h * 60 + m;
}

// Local date as YYYY-MM-DD (toISOString would use UTC and can be off by a day)
export function todayStr(offsetDays = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

// Checks that don't depend on which facility is chosen
export function validateSlot(
  role: Role,
  date: string,
  start: string,
  end: string
): string | null {
  if (!date || !start || !end) return "Please pick a date, start time and end time";

  const s = toMinutes(start);
  const e = toMinutes(end);

  if (e <= s) return "End time must be after start time";
  if (s % 30 !== 0 || e % 30 !== 0) return "Times must be on 30-minute slots";

  const maxDays = role === "Faculty" ? 14 : 7;
  if (date < todayStr()) return "You can't book a date in the past";
  if (date === todayStr()) {
    const now = new Date();
    if (s <= now.getHours() * 60 + now.getMinutes()) {
      return "That slot has already started";
    }
  }
  if (date > todayStr(maxDays)) {
    return `${role}s can book at most ${maxDays} days ahead`;
  }
  return null;
}

// Checks that depend on the facility type
export function validateDuration(
  role: Role,
  facility: Facility,
  start: string,
  end: string
): string | null {
  const hours = (toMinutes(end) - toMinutes(start)) / 60;

  if (role === "Student" && hours > 1) {
    return "Students may book at most 1 hour per booking";
  }
  if (role === "Faculty") {
    const max = facility.type === "Sports" ? 1 : 3;
    if (hours > max) {
      return `Faculty may book at most ${max} hour(s) for ${facility.type.toLowerCase()} facilities`;
    }
  }
  return null;
}

import type { Booking } from "../types";

export function startsAt(b: Booking): Date {
  return new Date(`${b.bookingDate}T${b.startTime}:00`);
}

export function isUpcoming(b: Booking): boolean {
  return (
    startsAt(b).getTime() > Date.now() &&
    (b.status === "Pending" || b.status === "Confirmed")
  );
}

// Cancel is allowed for Pending/Confirmed bookings starting 2+ hours from now
export function cancelBlockedReason(b: Booking): string | null {
  if (b.status !== "Pending" && b.status !== "Confirmed") {
    return "Only pending or confirmed bookings can be cancelled";
  }
  const msLeft = startsAt(b).getTime() - Date.now();
  if (msLeft < 2 * 60 * 60 * 1000) {
    return "Bookings can only be cancelled at least 2 hours before the start time";
  }
  return null;
}

export function timesOverlap(a: Booking, b: Booking): boolean {
  return (
    a.bookingDate === b.bookingDate &&
    toMinutes(a.startTime) < toMinutes(b.endTime) &&
    toMinutes(a.endTime) > toMinutes(b.startTime)
  );
}

