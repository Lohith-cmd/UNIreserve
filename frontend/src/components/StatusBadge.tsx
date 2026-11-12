import type { BookingStatus } from "../types";

export default function StatusBadge({ status }: { status: BookingStatus }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{status}</span>;
}