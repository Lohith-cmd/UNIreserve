import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  addHoliday,
  addMaintenance,
  deleteHoliday,
  deleteMaintenance,
  getFacilities,
  getHolidays,
  getMaintenance,
} from "../api";
import { getErrorMessage } from "../api/errors";
import { toMinutes } from "../utils/validation";
import type { Facility, Holiday, MaintenanceWindow } from "../types";

export default function AdminManage() {
  const [holidays, setHolidays] = useState<Holiday[]>([]);
  const [maintenance, setMaintenance] = useState<MaintenanceWindow[]>([]);
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [hDate, setHDate] = useState("");
  const [hDesc, setHDesc] = useState("");

  const [mFacility, setMFacility] = useState<number | "">("");
  const [mStartDate, setMStartDate] = useState("");
  const [mEndDate, setMEndDate] = useState("");
  const [mStartTime, setMStartTime] = useState("06:00");
  const [mEndTime, setMEndTime] = useState("22:00");
  const [mDesc, setMDesc] = useState("");

  const load = useCallback(async () => {
    try {
      const [h, m, f] = await Promise.all([getHolidays(), getMaintenance(), getFacilities()]);
      setHolidays(h);
      setMaintenance(m);
      setFacilities(f);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function run(action: () => Promise<unknown>, okMessage: string): Promise<boolean> {
    setError("");
    setSuccess("");
    setBusy(true);
    try {
      await action();
      setSuccess(okMessage);
      await load();
      return true;
    } catch (err) {
      setError(getErrorMessage(err));
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function submitHoliday(e: FormEvent) {
    e.preventDefault();
    if (!hDate) {
      setError("Pick a date for the holiday");
      return;
    }
    const ok = await run(() => addHoliday(hDate, hDesc.trim()), "Holiday added.");
    if (ok) {
      setHDate("");
      setHDesc("");
    }
  }

  async function submitMaintenance(e: FormEvent) {
    e.preventDefault();
    if (mFacility === "") {
      setError("Choose a facility");
      return;
    }
    if (!mStartDate || !mEndDate) {
      setError("Pick a start and end date");
      return;
    }
    if (mEndDate < mStartDate) {
      setError("End date can't be before the start date");
      return;
    }
    if (mEndDate === mStartDate && toMinutes(mEndTime) <= toMinutes(mStartTime)) {
      setError("End time must be after start time");
      return;
    }
    const ok = await run(
      () =>
        addMaintenance({
          facilityId: mFacility,
          startDate: mStartDate,
          endDate: mEndDate,
          startTime: mStartTime,
          endTime: mEndTime,
          description: mDesc.trim(),
        }),
      "Maintenance window added."
    );
    if (ok) {
      setMStartDate("");
      setMEndDate("");
      setMDesc("");
    }
  }

  function removeHoliday(h: Holiday) {
    if (!window.confirm(`Delete the holiday on ${h.holidayDate}?`)) return;
    run(() => deleteHoliday(h.holidayId), "Holiday deleted.");
  }

  function removeMaintenance(m: MaintenanceWindow) {
    if (!window.confirm(`Delete maintenance for ${m.facilityName}?`)) return;
    run(() => deleteMaintenance(m.scheduleId), "Maintenance window deleted.");
  }

  if (loading) return <p className="muted">Loading...</p>;

  return (
    <div>
      <h2>Manage</h2>

      {error && <div className="error-banner">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      <div className="card group">
        <h3 className="card-title">Holidays</h3>
        <form className="inline-form" onSubmit={submitHoliday}>
          <label>
            Date
            <input type="date" value={hDate} onChange={(e) => setHDate(e.target.value)} />
          </label>
          <label>
            Description
            <input
              type="text"
              maxLength={255}
              value={hDesc}
              onChange={(e) => setHDesc(e.target.value)}
            />
          </label>
          <button type="submit" disabled={busy}>
            Add holiday
          </button>
        </form>

        {holidays.length === 0 ? (
          <p className="muted">No holidays set.</p>
        ) : (
          holidays.map((h) => (
            <div className="list-row" key={h.holidayId}>
              <div>
                <strong>{h.holidayDate}</strong>
                <div className="muted">{h.description ?? "No description"}</div>
              </div>
              <button className="danger" disabled={busy} onClick={() => removeHoliday(h)}>
                Delete
              </button>
            </div>
          ))
        )}
      </div>

      <div className="card group">
        <h3 className="card-title">Maintenance schedules</h3>
        <form className="inline-form" onSubmit={submitMaintenance}>
          <label>
            Facility
            <select
              value={mFacility}
              onChange={(e) => setMFacility(e.target.value === "" ? "" : Number(e.target.value))}
            >
              <option value="">Select...</option>
              {facilities.map((f) => (
                <option key={f.facilityId} value={f.facilityId}>
                  {f.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Start date
            <input type="date" value={mStartDate} onChange={(e) => setMStartDate(e.target.value)} />
          </label>
          <label>
            End date
            <input type="date" value={mEndDate} onChange={(e) => setMEndDate(e.target.value)} />
          </label>
          <label>
            Start time
            <input
              type="time"
              step={1800}
              value={mStartTime}
              onChange={(e) => setMStartTime(e.target.value)}
            />
          </label>
          <label>
            End time
            <input
              type="time"
              step={1800}
              value={mEndTime}
              onChange={(e) => setMEndTime(e.target.value)}
            />
          </label>
          <label>
            Description
            <input
              type="text"
              maxLength={255}
              value={mDesc}
              onChange={(e) => setMDesc(e.target.value)}
            />
          </label>
          <button type="submit" disabled={busy}>
            Add window
          </button>
        </form>

        {maintenance.length === 0 ? (
          <p className="muted">No maintenance scheduled.</p>
        ) : (
          maintenance.map((m) => (
            <div className="list-row" key={m.scheduleId}>
              <div>
                <strong>{m.facilityName}</strong>
                <div className="muted">
                  {m.startDate} to {m.endDate}, {m.startTime} - {m.endTime}
                  {m.description ? ` · ${m.description}` : ""}
                </div>
              </div>
              <button className="danger" disabled={busy} onClick={() => removeMaintenance(m)}>
                Delete
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}