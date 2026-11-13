import { useEffect, useState } from "react";
import { getAnalytics } from "../api";
import { getErrorMessage } from "../api/errors";
import BarList from "../components/BarList";
import type { Analytics } from "../types";

const STATUSES = ["Pending", "Confirmed", "Rejected", "Cancelled", "Completed"];

export default function AdminAnalytics() {
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getAnalytics()
      .then(setData)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="muted">Loading...</p>;
  if (error) return <div className="error-banner">{error}</div>;
  if (!data) return null;

  const total = Object.values(data.statusCounts).reduce((a, b) => a + b, 0);
  const roles = Object.entries(data.roleBreakdown).map(([label, count]) => ({ label, count }));
  const weekly = [...data.weekly].sort(
    (a, b) => b.weekStart.localeCompare(a.weekStart) || a.facilityName.localeCompare(b.facilityName)
  );

  return (
    <div>
      <h2>Analytics</h2>

      <div className="stat-grid">
        <div className="card stat">
          <div className="stat-num">{total}</div>
          <div className="muted">Total requests</div>
        </div>
        {STATUSES.map((s) => (
          <div className="card stat" key={s}>
            <div className="stat-num">{data.statusCounts[s] ?? 0}</div>
            <div className="muted">{s}</div>
          </div>
        ))}
      </div>

      <div className="two-col">
        <div className="card">
          <h3 className="card-title">Most-booked facilities</h3>
          <BarList items={data.topFacilities} />
        </div>
        <div className="card">
          <h3 className="card-title">Busiest time slots</h3>
          <BarList items={data.peakHours} />
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
        {weekly.length === 0 ? (
          <p className="muted">No data yet.</p>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Week of</th>
                  <th>Facility</th>
                  <th>Total</th>
                  <th>Confirmed</th>
                  <th>Pending</th>
                  <th>Rejected</th>
                  <th>Cancelled</th>
                  <th>Hours</th>
                </tr>
              </thead>
              <tbody>
                {weekly.map((w) => (
                  <tr key={`${w.facilityId}-${w.weekStart}`}>
                    <td>{w.weekStart}</td>
                    <td>{w.facilityName}</td>
                    <td>{w.totalRequests}</td>
                    <td>{w.confirmed}</td>
                    <td>{w.pending}</td>
                    <td>{w.rejected}</td>
                    <td>{w.cancelled}</td>
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