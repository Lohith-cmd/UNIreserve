import { useCallback, useEffect, useState } from "react";
import { confirmBooking, getPendingBookings, rejectBooking } from "../api";
import { getErrorMessage } from "../api/errors";
import { timesOverlap } from "../utils/validation";
import type { PendingBooking } from "../types";

export default function AdminApprovals() {
  const [pending, setPending] = useState<PendingBooking[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

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

  async function act(b: PendingBooking, action: "confirm" | "reject") {
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

  const sorted = [...pending].sort(
    (a, b) =>
      a.facilityName.localeCompare(b.facilityName) ||
      a.bookingDate.localeCompare(b.bookingDate) ||
      a.startTime.localeCompare(b.startTime)
  );
  const facilityNames = Array.from(new Set(sorted.map((b) => b.facilityName)));

  return (
    <div>
      <h2>Pending Approvals</h2>

      {error && <div className="error-banner">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      {loading ? (
        <p className="muted">Loading...</p>
      ) : sorted.length === 0 ? (
        <p className="muted">No pending requests.</p>
      ) : (
        facilityNames.map((name) => {
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
                      const clashes = pending.filter(
                        (o) =>
                          o.bookingId !== b.bookingId &&
                          o.facilityId === b.facilityId &&
                          timesOverlap(o, b)
                      ).length;
                      return (
                        <div className="request-row" key={b.bookingId}>
                          <div>
                            <strong>
                              {b.startTime} - {b.endTime}
                            </strong>
                            <div className="muted">
                              {b.userName} ({b.userRole})
                            </div>
                            {clashes > 0 && (
                              <div className="warn">
                                Overlaps with {clashes} other request(s)
                              </div>
                            )}
                          </div>
                          <div className="booking-actions">
                            <button
                              disabled={busyId !== null}
                              onClick={() => act(b, "confirm")}
                            >
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
        })
      )}
    </div>
  );
}