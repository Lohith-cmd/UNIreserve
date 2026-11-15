// The backend can send timestamps without a timezone (e.g. "2026-11-12T10:30:00").
// The database stores UTC, so we treat those as UTC. Otherwise the browser reads
// them as local time and everything shows hours off.
export function parseServerDate(s: string): Date {
  const iso = s.replace(" ", "T");
  const hasZone = /(Z|[+-]\d{2}:?\d{2})$/i.test(iso);
  return new Date(hasZone ? iso : `${iso}Z`);
}

export function formatDateTime(s: string): string {
  const d = parseServerDate(s);
  if (isNaN(d.getTime())) return s;
  return d.toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function timeAgo(s: string): string {
  const t = parseServerDate(s).getTime();
  if (isNaN(t)) return "";
  const mins = Math.round((Date.now() - t) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} h ago`;
  return `${Math.floor(hrs / 24)} d ago`;
}