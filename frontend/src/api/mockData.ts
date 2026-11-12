import type { Booking, Facility, User } from "../types";

export function dateFromToday(offsetDays: number): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10);
}

export const mockUsers: User[] = [
  { userId: 1, name: "Admin User", email: "admin@uni.edu", role: "Admin" },
  { userId: 2, name: "Dr. Faculty", email: "faculty@uni.edu", role: "Faculty" },
  { userId: 4, name: "Student One", email: "student@uni.edu", role: "Student" },
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
    bookingId: 1,
    userId: 4,
    facilityId: 1,
    facilityName: "Badminton Court A",
    bookingDate: dateFromToday(1),
    startTime: "17:00",
    endTime: "18:00",
    status: "Confirmed",
  },
  {
    bookingId: 2,
    userId: 4,
    facilityId: 2,
    facilityName: "Basketball Court",
    bookingDate: dateFromToday(2),
    startTime: "16:00",
    endTime: "17:00",
    status: "Pending",
  },
  {
    bookingId: 3,
    userId: 4,
    facilityId: 1,
    facilityName: "Badminton Court A",
    bookingDate: dateFromToday(-5),
    startTime: "10:00",
    endTime: "11:00",
    status: "Rejected",
  },
];