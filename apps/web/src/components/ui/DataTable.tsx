import * as React from "react";
import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

export interface TableColumn<T> {
  key: keyof T;
  header: string;
  render?: (value: T[keyof T], row: T) => ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: TableColumn<T>[];
  emptyLabel?: string;
  className?: string;
}

export function DataTable<T>({ data, columns, emptyLabel = "No data", className }: DataTableProps<T>) {
  if (!data.length) {
    return <div className="text-center text-sm text-brand-ink/60">{emptyLabel}</div>;
  }

  return (
    <div className={cn("overflow-hidden rounded-3xl border border-white/70 bg-white", className)}>
      <table className="w-full text-left text-sm">
        <thead className="bg-brand-shell/70 text-brand-ink/70">
          <tr>
            {columns.map((col) => (
              <th key={col.header} className={cn("px-5 py-3 font-semibold", col.className)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-t border-white/70 text-brand-ink">
              {columns.map((col) => (
                <td key={String(col.key)} className={cn("px-5 py-4", col.className)}>
                  {col.render ? col.render(row[col.key], row) : (row[col.key] as React.ReactNode)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
