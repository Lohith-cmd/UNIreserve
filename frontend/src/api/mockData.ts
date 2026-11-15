import type { Booking, Facility, StatusLogEntry, User } from "../types";

export function dateFromToday(offsetDays: number): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10);
}

export const mockUsers: User[] = [
  { userId: 1, name: "Admin User", email: "admin@uni.edu", role: "Admin" },
  { userId: 2, name: "Dr. Faculty", email: "faculty@uni.edu", role: "Faculty" },
  { userId: 3, name: "Dr. Faculty Two", email: "faculty2@uni.edu", role: "Faculty" },
  { userId: 4, name: "Student One", email: "student@uni.edu", role: "Student" },
  { userId: 5, name: "Student Two", email: "student2@uni.edu", role: "Student" },
  { userId: 6, name: "Student Three", email: "student3@uni.edu", role: "Student" },
];

export const mockFacilities: Facility[] = [
  { facilityId: 1, name: "Badminton Court A", type: "Sports", status: "Active" },
  { facilityId: 2, name: "Basketball Court", type: "Sports", status: "Active" },
  { facilityId: 3, name: "Tennis Court", type: "Sports", status: "Under Maintenance" },
  { facilityId: 4, name: "Classroom C101", type: "Classroom", status: "Active" },
  { facilityId: 5, name: "Classroom C102", type: "Classroom", status: "Active" },
];

export const mockBookings: Booking[] = [
  {
    bookingId: 1, userId: 4, facilityId: 1, facilityName: "Badminton Court A",
    bookingDate: dateFromToday(1), startTime: "17:00", endTime: "18:00", status: "Confirmed",
  },
  {
    bookingId: 2, userId: 4, facilityId: 2, facilityName: "Basketball Court",
    bookingDate: dateFromToday(2), startTime: "16:00", endTime: "17:00", status: "Pending",
  },
  {
    bookingId: 3, userId: 4, facilityId: 1, facilityName: "Badminton Court A",
    bookingDate: dateFromToday(-5), startTime: "10:00", endTime: "11:00", status: "Rejected",
  },
  {
    bookingId: 4, userId: 5, facilityId: 2, facilityName: "Basketball Court",
    bookingDate: dateFromToday(2), startTime: "16:30", endTime: "17:30", status: "Pending",
  },
  {
    bookingId: 5, userId: 6, facilityId: 2, facilityName: "Basketball Court",
    bookingDate: dateFromToday(2), startTime: "16:00", endTime: "17:00", status: "Pending",
  },
  {
    bookingId: 6, userId: 2, facilityId: 4, facilityName: "Classroom C101",
    bookingDate: dateFromToday(3), startTime: "18:00", endTime: "20:00", status: "Pending",
  },
  {
    bookingId: 7, userId: 6, facilityId: 1, facilityName: "Badminton Court A",
    bookingDate: dateFromToday(1), startTime: "17:00", endTime: "18:00", status: "Pending",
  },
];

const ago = (hours: number) =>
  new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();

export const mockLogs: StatusLogEntry[] = [
  { logId: 1, bookingId: 1, oldStatus: null, newStatus: "Pending", changedAt: ago(30), changedBy: 4 },
  { logId: 2, bookingId: 1, oldStatus: "Pending", newStatus: "Confirmed", changedAt: ago(26), changedBy: 1 },
  { logId: 3, bookingId: 2, oldStatus: null, newStatus: "Pending", changedAt: ago(5), changedBy: 4 },
  { logId: 4, bookingId: 3, oldStatus: null, newStatus: "Pending", changedAt: ago(130), changedBy: 4 },
  { logId: 5, bookingId: 3, oldStatus: "Pending", newStatus: "Rejected", changedAt: ago(120), changedBy: 1 },
  { logId: 6, bookingId: 4, oldStatus: null, newStatus: "Pending", changedAt: ago(4), changedBy: 5 },
  { logId: 7, bookingId: 5, oldStatus: null, newStatus: "Pending", changedAt: ago(3), changedBy: 6 },
  { logId: 8, bookingId: 6, oldStatus: null, newStatus: "Pending", changedAt: ago(2), changedBy: 2 },
  { logId: 9, bookingId: 7, oldStatus: null, newStatus: "Pending", changedAt: ago(1), changedBy: 6 },
];