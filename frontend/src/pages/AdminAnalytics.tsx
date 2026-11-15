import { useEffect, useState } from "react";
import { getAnalytics } from "../api";
import { getErrorMessage } from "../api/errors";
import BarList from "../components/BarList";
import type { Analytics } from "../types";

type StatusKey = "Pending" | "Confirmed" | "Rejected" | "Cancelled";

// The weekly stats only have columns for these four, so "Completed" can't be filtered.
const FIELD = {
  Pending: "pending",
  Confirmed: "confirmed",
  Rejected: "rejected",
  Cancelled: "cancelled",
} as const;

const STATUSES = ["Pending", "Confirmed", "Rejected", "Cancelled", "Completed"];

function StatCard({
  label,
  value,
  active,
  onClick,
}: {
  label: string;
  value: number;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <div
      className={`card stat${onClick ? " clickable" : ""}${active ? " active" : ""}`}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      onKeyDown={
        onClick
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onClick();
              }
            }
          : undefined
      }
    >
      <div className="stat-num">{value}</div>
      <div className="muted">{label}</div>
    </div>
  );
}

export default function AdminAnalytics() {
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusKey | null>(null);
  const [facilityFilter, setFacilityFilter] = useState<string | null>(null);

  useEffect(() => {
    getAnalytics()
      .then(setData)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="muted">Loading...</p>;
  if (error) return <div className="error-banner">{error}</div>;
  if (!data) return null;

  const field = statusFilter ? FIELD[statusFilter] : null;
  const total = Object.values(data.statusCounts).reduce((a, b) => a + b, 0);
  const roles = Object.entries(data.roleBreakdown).map(([label, count]) => ({ label, count }));

  // With a status selected, rebuild the facility ranking from the weekly rows
  let facilityBars = data.topFacilities;
  if (field) {
    const sums = new Map<string, number>();
    for (const w of data.weekly) {
      sums.set(w.facilityName, (sums.get(w.facilityName) ?? 0) + w[field]);
    }
    facilityBars = [...sums.entries()]
      .map(([label, count]) => ({ label, count }))
      .filter((i) => i.count > 0)
      .sort((a, b) => b.count - a.count);
  }

  const rows = data.weekly
    .filter(
      (w) =>
        (!facilityFilter || w.facilityName === facilityFilter) && (!field || w[field] > 0)
    )
    .sort((a, b) =>
      field
        ? b[field] - a[field] || b.weekStart.localeCompare(a.weekStart)
        : b.weekStart.localeCompare(a.weekStart) || a.facilityName.localeCompare(b.facilityName)
    );

  function clearAll() {
    setStatusFilter(null);
    setFacilityFilter(null);
  }

  return (
    <div>
      <h2>Analytics</h2>

      <div className="stat-grid">
        <StatCard
          label="Total requests"
          value={total}
          active={!statusFilter}
          onClick={() => setStatusFilter(null)}
        />
        {STATUSES.map((s) => {
          const filterable = s in FIELD;
          return (
            <StatCard
              key={s}
              label={s}
              value={data.statusCounts[s] ?? 0}
              active={statusFilter === s}
              onClick={
                filterable
                  ? () => setStatusFilter((prev) => (prev === s ? null : (s as StatusKey)))
                  : undefined
              }
            />
          );
        })}
      </div>

      {(statusFilter || facilityFilter) && (
        <div className="filter-chips">
          <span className="muted">Filtering:</span>
          {statusFilter && <span className="chip">{statusFilter}</span>}
          {facilityFilter && <span className="chip">{facilityFilter}</span>}
          <button className="secondary" onClick={clearAll}>
            Clear
          </button>
        </div>
      )}

      <div className="two-col">
        <div className="card">
          <h3 className="card-title">Most-booked facilities</h3>
          <BarList
            items={facilityBars}
            selected={facilityFilter}
            onSelect={(label) => setFacilityFilter((prev) => (prev === label ? null : label))}
            emptyText="No facilities for this status."
          />
          <p className="muted hint">Click a facility to filter the weekly table.</p>
        </div>
        <div className="card">
          <h3 className="card-title">Busiest time slots</h3>
          <BarList items={data.peakHours} />
          {statusFilter && (
            <p className="muted hint">Busiest slots and roles always count all statuses.</p>
          )}
        </div>
      </div>

      <div className="two-col">
        <div className="card">
          <h3 className="card-title">Requests by user role</h3>
          <BarList items={roles} />
        </div>
      </div>

      <div className="card">
        <h3 className="card-title">Weekly summary by facility</h3>
        {rows.length === 0 ? (
          <p className="muted">No rows match these filters.</p>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Week of</th>
                  <th>Facility</th>
                  <th>Total</th>
                  <th className={field === "confirmed" ? "hl" : undefined}>Confirmed</th>
                  <th className={field === "pending" ? "hl" : undefined}>Pending</th>
                  <th className={field === "rejected" ? "hl" : undefined}>Rejected</th>
                  <th className={field === "cancelled" ? "hl" : undefined}>Cancelled</th>
                  <th>Hours</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((w) => (
                  <tr key={`${w.facilityId}-${w.weekStart}`}>
                    <td>{w.weekStart}</td>
                    <td>{w.facilityName}</td>
                    <td>{w.totalRequests}</td>
                    <td className={field === "confirmed" ? "hl" : undefined}>{w.confirmed}</td>
                    <td className={field === "pending" ? "hl" : undefined}>{w.pending}</td>
                    <td className={field === "rejected" ? "hl" : undefined}>{w.rejected}</td>
                    <td className={field === "cancelled" ? "hl" : undefined}>{w.cancelled}</td>
                    <td>{w.bookedHours.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}