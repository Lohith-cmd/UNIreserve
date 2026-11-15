import { useCallback, useEffect, useMemo, useState } from "react";
import { confirmBooking, getPendingBookings, rejectBooking } from "../api";
import { getErrorMessage } from "../api/errors";
import { formatDateTime, parseServerDate, timeAgo } from "../utils/format";
import { timesOverlap, toMinutes } from "../utils/validation";
import type { PendingBooking } from "../types";

type SortMode = "requested" | "slot";

const requestedAt = (b: PendingBooking) => parseServerDate(b.createdAt).getTime() || 0;

export default function AdminApprovals() {
  const [pending, setPending] = useState<PendingBooking[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [fDate, setFDate] = useState("");
  const [fFrom, setFFrom] = useState("");
  const [fTo, setFTo] = useState("");
  const [fFacility, setFFacility] = useState("");
  const [sort, setSort] = useState<SortMode>("requested");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setPending(await getPendingBookings());
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Position in the request queue for each facility + day (1 = asked first)
  const rankById = useMemo(() => {
    const groups = new Map<string, PendingBooking[]>();
    for (const b of pending) {
      const key = `${b.facilityId}|${b.bookingDate}`;
      groups.set(key, [...(groups.get(key) ?? []), b]);
    }
    const ranks = new Map<number, number>();
    groups.forEach((list) => {
      [...list]
        .sort((a, c) => requestedAt(a) - requestedAt(c))
        .forEach((b, i) => ranks.set(b.bookingId, i + 1));
    });
    return ranks;
  }, [pending]);

  const overlapsWith = (b: PendingBooking) =>
    pending.filter(
      (o) => o.bookingId !== b.bookingId && o.facilityId === b.facilityId && timesOverlap(o, b)
    );

  async function act(b: PendingBooking, action: "confirm" | "reject") {
    if (action === "confirm") {
      const earlier = overlapsWith(b)
        .filter((o) => requestedAt(o) < requestedAt(b))
        .sort((x, y) => requestedAt(x) - requestedAt(y))[0];
      if (
        earlier &&
        !window.confirm(
          `${earlier.userName} asked for an overlapping slot earlier (${timeAgo(earlier.createdAt)}). Confirm ${b.userName}'s request anyway?`
        )
      ) {
        return;
      }
    }

    setError("");
    setSuccess("");
    setBusyId(b.bookingId);
    try {
      if (action === "confirm") {
        const res = await confirmBooking(b.bookingId);
        const n = res.autoRejected ?? 0;
        setSuccess(
          n > 0
            ? `Confirmed. ${n} overlapping request(s) were automatically rejected.`
            : res.message ?? "Confirmed."
        );
      } else {
        await rejectBooking(b.bookingId);
        setSuccess("Request rejected.");
      }
      await load();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  function clearFilters() {
    setFDate("");
    setFFrom("");
    setFTo("");
    setFFacility("");
  }

  const facilityOptions = Array.from(new Set(pending.map((b) => b.facilityName))).sort();

  // "Slot from/to" keeps requests whose slot overlaps that window
  const filtered = pending.filter((b) => {
    if (fFacility && b.facilityName !== fFacility) return false;
    if (fDate && b.bookingDate !== fDate) return false;
    if (fFrom && toMinutes(b.endTime) <= toMinutes(fFrom)) return false;
    if (fTo && toMinutes(b.startTime) >= toMinutes(fTo)) return false;
    return true;
  });

  const sorted = [...filtered].sort(
    (a, b) =>
      a.facilityName.localeCompare(b.facilityName) ||
      a.bookingDate.localeCompare(b.bookingDate) ||
      (sort === "requested"
        ? requestedAt(a) - requestedAt(b)
        : a.startTime.localeCompare(b.startTime) || requestedAt(a) - requestedAt(b))
  );
  const facilityNames = Array.from(new Set(sorted.map((b) => b.facilityName)));

  return (
    <div>
      <h2>Pending Approvals</h2>

      <div className="card filters">
        <label>
          Date
          <input type="date" value={fDate} onChange={(e) => setFDate(e.target.value)} />
        </label>
        <label>
          Slot from
          <input type="time" value={fFrom} onChange={(e) => setFFrom(e.target.value)} />
        </label>
        <label>
          Slot to
          <input type="time" value={fTo} onChange={(e) => setFTo(e.target.value)} />
        </label>
        <label>
          Facility
          <select value={fFacility} onChange={(e) => setFFacility(e.target.value)}>
            <option value="">All</option>
            {facilityOptions.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
        <label>
          Order within a day
          <select value={sort} onChange={(e) => setSort(e.target.value as SortMode)}>
            <option value="requested">Earliest request first</option>
            <option value="slot">Slot time</option>
          </select>
        </label>
        <button className="secondary" onClick={clearFilters}>
          Clear filters
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      {loading ? (
        <p className="muted">Loading...</p>
      ) : sorted.length === 0 ? (
        <p className="muted">
          {pending.length === 0 ? "No pending requests." : "No requests match these filters."}
        </p>
      ) : (
        <>
          <p className="muted">
            Showing {sorted.length} of {pending.length} pending requests
          </p>
          {facilityNames.map((name) => {
            const ofFacility = sorted.filter((b) => b.facilityName === name);
            const dates = Array.from(new Set(ofFacility.map((b) => b.bookingDate)));
            return (
              <div className="card group" key={name}>
                <h3 className="group-title">{name}</h3>
                {dates.map((date) => (
                  <div key={date}>
                    <div className="date-title">{date}</div>
                    {ofFacility
                      .filter((b) => b.bookingDate === date)
                      .map((b) => {
                        const clashes = overlapsWith(b);
                        const earlier = clashes.filter((o) => requestedAt(o) < requestedAt(b)).length;
                        const later = clashes.length - earlier;
                        return (
                          <div className="request-row" key={b.bookingId}>
                            <div>
                              <div className="req-title">
                                <span className="rank">#{rankById.get(b.bookingId)}</span>
                                <strong>
                                  {b.startTime} - {b.endTime}
                                </strong>
                              </div>
                              <div className="muted">
                                {b.userName} ({b.userRole})
                              </div>
                              {b.createdAt && (
                                <div className="muted">
                                  Requested {formatDateTime(b.createdAt)} · {timeAgo(b.createdAt)}
                                </div>
                              )}
                              {earlier > 0 && (
                                <div className="warn">{earlier} earlier overlapping request(s)</div>
                              )}
                              {earlier === 0 && later > 0 && (
                                <div className="ok">
                                  First in line · {later} later overlapping request(s)
                                </div>
                              )}
                            </div>
                            <div className="booking-actions">
                              <button disabled={busyId !== null} onClick={() => act(b, "confirm")}>
                                {busyId === b.bookingId ? "..." : "Confirm"}
                              </button>
                              <button
                                className="danger"
                                disabled={busyId !== null}
                                onClick={() => act(b, "reject")}
                              >
                                Reject
                              </button>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                ))}
              </div>
            );
          })}
        </>
      )}
    </div>
  );
}