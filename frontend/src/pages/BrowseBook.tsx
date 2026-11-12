import { useState, type FormEvent } from "react";
import { createBooking, searchAvailability } from "../api";
import { getErrorMessage } from "../api/errors";
import { useAuth } from "../context/useAuth";
import { todayStr, validateDuration, validateSlot } from "../utils/validation";
import type { Facility, FacilityType } from "../types";

export default function BrowseBook() {
  const { user } = useAuth();
  const role = user!.role;

  const [date, setDate] = useState(todayStr(1));
  const [startTime, setStartTime] = useState("17:00");
  const [endTime, setEndTime] = useState("18:00");
  const [type, setType] = useState<FacilityType | "">("");

  const [results, setResults] = useState<Facility[] | null>(null);
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
      const found = await searchAvailability({
        date,
        startTime,
        endTime,
        type: type || undefined,
      });
      setResults(found);
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
            results.map((f) => (
              <div className="card facility-row" key={f.facilityId}>
                <div>
                  <strong>{f.name}</strong>
                  <div className="muted">{f.type}</div>
                </div>
                <button
                  onClick={() => handleBook(f)}
                  disabled={bookingId !== null}
                >
                  {bookingId === f.facilityId ? "Requesting..." : "Request booking"}
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}