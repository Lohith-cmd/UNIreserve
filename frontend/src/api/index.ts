import http from "./http";
import { mockBookings, mockFacilities, mockUsers } from "./mockData";
import type { Booking, Facility, FacilityType, LoginResponse, User } from "../types";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

const delay = (ms = 400) => new Promise((resolve) => setTimeout(resolve, ms));

const toMinutes = (t: string) => {
  const [h, m] = t.split(":").map(Number);
  return h * 60 + m;
};

function currentMockUser(): User {
  const token = localStorage.getItem("token") ?? "";
  const id = Number(token.replace("mock-token-", ""));
  const user = mockUsers.find((u) => u.userId === id);
  if (!user) throw new Error("Not logged in");
  return user;
}

export interface AvailabilityQuery {
  date: string;
  startTime: string;
  endTime: string;
  type?: FacilityType;
}

export interface NewBooking {
  facilityId: number;
  bookingDate: string;
  startTime: string;
  endTime: string;
}

// ---------- Auth ----------
export async function login(email: string, password: string): Promise<LoginResponse> {
  if (USE_MOCK) {
    await delay();
    const user = mockUsers.find((u) => u.email === email);
    if (!user) throw new Error("Invalid email or password");
    return { token: `mock-token-${user.userId}`, user };
  }
  const res = await http.post<LoginResponse>("/auth/login", { email, password });
  return res.data;
}

// ---------- Facilities ----------
export async function getFacilities(): Promise<Facility[]> {
  if (USE_MOCK) {
    await delay();
    return [...mockFacilities];
  }
  const res = await http.get<Facility[]>("/facilities");
  return res.data;
}

export async function searchAvailability(q: AvailabilityQuery): Promise<Facility[]> {
  if (USE_MOCK) {
    await delay();
    return mockFacilities.filter((f) => {
      if (f.status !== "Active") return false;
      if (q.type && f.type !== q.type) return false;
      const clash = mockBookings.some(
        (b) =>
          b.facilityId === f.facilityId &&
          b.bookingDate === q.date &&
          b.status === "Confirmed" &&
          toMinutes(q.startTime) < toMinutes(b.endTime) &&
          toMinutes(q.endTime) > toMinutes(b.startTime)
      );
      return !clash;
    });
  }
  const res = await http.get<Facility[]>("/facilities/availability", { params: q });
  return res.data;
}

// ---------- Bookings ----------
export async function createBooking(input: NewBooking): Promise<Booking> {
  if (USE_MOCK) {
    await delay();
    const user = currentMockUser();
    const facility = mockFacilities.find((f) => f.facilityId === input.facilityId);
    if (!facility) throw new Error("Facility not found");

    const start = toMinutes(input.startTime);
    const end = toMinutes(input.endTime);
    const hours = (end - start) / 60;

    if (end <= start) throw new Error("End time must be after start time");
    if (start % 30 !== 0 || end % 30 !== 0) throw new Error("Bookings must use 30-minute slots");

    if (user.role === "Student" && hours > 1) {
      throw new Error("Students may book at most 1 hour per booking");
    }
    if (user.role === "Faculty") {
      const max = facility.type === "Sports" ? 1 : 3;
      if (hours > max) throw new Error(`Faculty may book at most ${max} hour(s) for this facility`);
    }

    const booking: Booking = {
      bookingId: mockBookings.length + 1,
      userId: user.userId,
      facilityId: facility.facilityId,
      facilityName: facility.name,
      bookingDate: input.bookingDate,
      startTime: input.startTime,
      endTime: input.endTime,
      status: "Pending",
    };
    mockBookings.push(booking);
    return booking;
  }
  const res = await http.post<Booking>("/bookings", input);
  return res.data;
}

export async function getMyBookings(): Promise<Booking[]> {
  if (USE_MOCK) {
    await delay();
    const user = currentMockUser();
    return mockBookings.filter((b) => b.userId === user.userId);
  }
  const res = await http.get<Booking[]>("/bookings/me");
  return res.data;
}

export async function cancelBooking(bookingId: number): Promise<void> {
  if (USE_MOCK) {
    await delay();
    const b = mockBookings.find((x) => x.bookingId === bookingId);
    if (!b) throw new Error("Booking not found");
    b.status = "Cancelled";
    return;
  }
  await http.post(`/bookings/${bookingId}/cancel`);
}