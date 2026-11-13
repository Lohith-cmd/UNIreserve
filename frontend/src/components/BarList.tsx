import type { RankedItem } from "../types";

export default function BarList({
  items,
  emptyText = "No data yet.",
}: {
  items: RankedItem[];
  emptyText?: string;
}) {
  if (items.length === 0) return <p className="muted">{emptyText}</p>;
  const max = Math.max(...items.map((i) => i.count), 1);

  return (
    <div className="bar-list">
      {items.map((i, idx) => (
        <div className="bar-row" key={`${i.label}-${idx}`}>
          <span className="bar-label" title={i.label}>
            {i.label}
          </span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(i.count / max) * 100}%` }} />
          </div>
          <span className="bar-count">{i.count}</span>
        </div>
      ))}
    </div>
  );
}