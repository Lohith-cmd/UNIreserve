import { useState, type FormEvent } from "react";
import { createBooking, getMyBookings, searchAvailability } from "../api";
import { getErrorMessage } from "../api/errors";
import { useAuth } from "../context/useAuth";
import StatusBadge from "../components/StatusBadge";
import {
  findMyConflict,
  todayStr,
  validateDuration,
  validateSlot,
} from "../utils/validation";
import type { Booking, Facility, FacilityType } from "../types";

export default function BrowseBook() {
  const { user } = useAuth();
  const role = user!.role;

  const [date, setDate] = useState(todayStr(1));
  const [startTime, setStartTime] = useState("17:00");
  const [endTime, setEndTime] = useState("18:00");
  const [type, setType] = useState<FacilityType | "">("");

  const [results, setResults] = useState<Facility[] | null>(null);
  const [mine, setMine] = useState<Booking[]>([]);
  const [searching, setSearching] = useState(false);
  const [bookingId, setBookingId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSearch(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");

    const problem = validateSlot(role, date, startTime, endTime);
    if (problem) {
      setError(problem);
      return;
    }

    setSearching(true);
    try {
      const [found, myBookings] = await Promise.all([
        searchAvailability({ date, startTime, endTime, type: type || undefined }),
        getMyBookings(),
      ]);
      setResults(found);
      setMine(myBookings);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSearching(false);
    }
  }

  async function handleBook(facility: Facility) {
    setError("");
    setSuccess("");

    const problem =
      validateSlot(role, date, startTime, endTime) ??
      validateDuration(role, facility, startTime, endTime);
    if (problem) {
      setError(problem);
      return;
    }

    const existing = findMyConflict(mine, facility.facilityId, date, startTime, endTime);
    if (existing) {
      setError(
        `You already have a ${existing.status.toLowerCase()} request for ${facility.name} at this time.`
      );
      return;
    }

    setBookingId(facility.facilityId);
    try {
      await createBooking({
        facilityId: facility.facilityId,
        bookingDate: date,
        startTime,
        endTime,
      });
      setSuccess(
        `Request sent for ${facility.name} on ${date}, ${startTime}-${endTime}. It is pending admin approval.`
      );
      setMine(await getMyBookings()); // flips this row to "Pending" right away
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBookingId(null);
    }
  }

  return (
    <div>
      <h2>Browse &amp; Book</h2>

      <form className="card filters" onSubmit={handleSearch}>
        <label>
          Date
          <input
            type="date"
            value={date}
            min={todayStr()}
            onChange={(e) => setDate(e.target.value)}
            required
          />
        </label>
        <label>
          Start time
          <input
            type="time"
            step={1800}
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            required
          />
        </label>
        <label>
          End time
          <input
            type="time"
            step={1800}
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
            required
          />
        </label>
        <label>
          Facility type
          <select
            value={type}
            onChange={(e) => setType(e.target.value as FacilityType | "")}
          >
            <option value="">All</option>
            <option value="Sports">Sports</option>
            <option value="Classroom">Classroom</option>
            <option value="Other">Other</option>
          </select>
        </label>
        <button type="submit" disabled={searching}>
          {searching ? "Searching..." : "Search"}
        </button>
      </form>

      {error && <div className="error-banner">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      {results && (
        <div className="facility-list">
          {results.length === 0 ? (
            <p className="muted">No facilities available for that slot.</p>
          ) : (
            results.map((f) => {
              const existing = findMyConflict(
                mine,
                f.facilityId,
                date,
                startTime,
                endTime
              );
              return (
                <div className="card facility-row" key={f.facilityId}>
                  <div>
                    <strong>{f.name}</strong>
                    <div className="muted">
                      {f.type}
                      {f.location ? ` · ${f.location}` : ""}
                      {f.pendingRequests
                        ? ` · ${f.pendingRequests} pending request(s)`
                        : ""}
                    </div>
                  </div>

                  {existing ? (
                    <div className="existing-request">
                      <StatusBadge status={existing.status} />
                      <span className="muted">
                        {existing.status === "Pending"
                          ? "You've already requested this slot"
                          : "You already have this slot booked"}
                      </span>
                    </div>
                  ) : (
                    <button
                      onClick={() => handleBook(f)}
                      disabled={bookingId !== null}
                    >
                      {bookingId === f.facilityId ? "Requesting..." : "Request booking"}
                    </button>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}