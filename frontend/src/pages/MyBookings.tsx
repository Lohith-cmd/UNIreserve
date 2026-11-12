import { useCallback, useEffect, useState } from "react";
import { cancelBooking, getBookingLog, getMyBookings } from "../api";
import { getErrorMessage } from "../api/errors";
import StatusBadge from "../components/StatusBadge";
import { cancelBlockedReason, isUpcoming, startsAt } from "../utils/validation";
import type { Booking, StatusLogEntry } from "../types";

type Tab = "upcoming" | "history";

export default function MyBookings() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("upcoming");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [cancellingId, setCancellingId] = useState<number | null>(null);
  const [openLogId, setOpenLogId] = useState<number | null>(null);
  const [logs, setLogs] = useState<Record<number, StatusLogEntry[]>>({});

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setBookings(await getMyBookings());
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const upcoming = bookings
    .filter(isUpcoming)
    .sort((a, b) => startsAt(a).getTime() - startsAt(b).getTime());
  const history = bookings
    .filter((b) => !isUpcoming(b))
    .sort((a, b) => startsAt(b).getTime() - startsAt(a).getTime());
  const shown = tab === "upcoming" ? upcoming : history;

  async function handleCancel(b: Booking) {
    if (!window.confirm(`Cancel ${b.facilityName} on ${b.bookingDate}?`)) return;
    setError("");
    setSuccess("");
    setCancellingId(b.bookingId);
    try {
      await cancelBooking(b.bookingId);
      setSuccess("Booking cancelled.");
      setLogs((prev) => {
        const copy = { ...prev };
        delete copy[b.bookingId]; // force a fresh timeline fetch
        return copy;
      });
      await load();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setCancellingId(null);
    }
  }

  async function toggleTimeline(id: number) {
    if (openLogId === id) {
      setOpenLogId(null);
      return;
    }
    setOpenLogId(id);
    if (!logs[id]) {
      try {
        const entries = await getBookingLog(id);
        setLogs((prev) => ({ ...prev, [id]: entries }));
      } catch (err) {
        setError(getErrorMessage(err));
      }
    }
  }

  return (
    <div>
      <h2>My Bookings</h2>

      <div className="tabs">
        <button
          className={tab === "upcoming" ? "tab active" : "tab"}
          onClick={() => setTab("upcoming")}
        >
          Upcoming ({upcoming.length})
        </button>
        <button
          className={tab === "history" ? "tab active" : "tab"}
          onClick={() => setTab("history")}
        >
          History ({history.length})
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      {loading ? (
        <p className="muted">Loading...</p>
      ) : shown.length === 0 ? (
        <p className="muted">
          {tab === "upcoming" ? "No upcoming bookings." : "No past bookings yet."}
        </p>
      ) : (
        <div className="facility-list">
          {shown.map((b) => {
            const blocked = cancelBlockedReason(b);
            const canCancelNow = tab === "upcoming" && blocked === null;
            return (
              <div className="card" key={b.bookingId}>
                <div className="booking-head">
                  <div>
                    <strong>{b.facilityName}</strong>
                    <div className="muted">
                      {b.bookingDate}, {b.startTime} - {b.endTime}
                    </div>
                  </div>
                  <StatusBadge status={b.status} />
                </div>

                <div className="booking-actions">
                  <button className="secondary" onClick={() => toggleTimeline(b.bookingId)}>
                    {openLogId === b.bookingId ? "Hide timeline" : "View timeline"}
                  </button>
                  {tab === "upcoming" && (
                    <button
                      className="danger"
                      disabled={!canCancelNow || cancellingId === b.bookingId}
                      title={blocked ?? ""}
                      onClick={() => handleCancel(b)}
                    >
                      {cancellingId === b.bookingId ? "Cancelling..." : "Cancel"}
                    </button>
                  )}
                </div>
                {tab === "upcoming" && blocked && (
                  <div className="muted hint">{blocked}</div>
                )}

                {openLogId === b.bookingId && (
                  <ul className="timeline">
                    {!logs[b.bookingId] ? (
                      <li className="muted">Loading...</li>
                    ) : (
                      logs[b.bookingId].map((l) => (
                        <li key={l.logId}>
                          <StatusBadge status={l.newStatus} />
                          <span className="muted">
                            {l.oldStatus ? `from ${l.oldStatus} · ` : "created · "}
                            {new Date(l.changedAt).toLocaleString()}
                          </span>
                        </li>
                      ))
                    )}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}