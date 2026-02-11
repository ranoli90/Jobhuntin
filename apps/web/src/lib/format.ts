export function formatCurrency(value?: number | null, locale?: string, currency: string = "USD") {
  if (value == null || Number.isNaN(value)) return "–";
  try {
    const fmt = new Intl.NumberFormat(locale || undefined, {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    });
    return fmt.format(value);
  } catch (err) {
    return `$${Math.round(value).toLocaleString()}`;
  }
}

export function formatDate(value?: string | number | Date | null, locale?: string, opts?: Intl.DateTimeFormatOptions) {
  if (!value) return "–";
  try {
    const d = value instanceof Date ? value : new Date(value);
    return new Intl.DateTimeFormat(locale || undefined, opts || { dateStyle: "medium" }).format(d);
  } catch {
    return typeof value === "string" ? value : "–";
  }
}
