import type { RankedItem } from "../types";

export default function BarList({
  items,
  emptyText = "No data yet.",
  selected,
  onSelect,
}: {
  items: RankedItem[];
  emptyText?: string;
  selected?: string | null;
  onSelect?: (label: string) => void;
}) {
  if (items.length === 0) return <p className="muted">{emptyText}</p>;
  const max = Math.max(...items.map((i) => i.count), 1);
  const select = onSelect;

  return (
    <div className="bar-list">
      {items.map((i, idx) => (
        <div
          className={`bar-row${select ? " clickable" : ""}${selected === i.label ? " selected" : ""}`}
          key={`${i.label}-${idx}`}
          role={select ? "button" : undefined}
          tabIndex={select ? 0 : undefined}
          onClick={select ? () => select(i.label) : undefined}
          onKeyDown={
            select
              ? (e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    select(i.label);
                  }
                }
              : undefined
          }
        >
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