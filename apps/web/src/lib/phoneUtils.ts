/**
 * Formats a phone number with flexible international support.
 * US numbers: (XXX) XXX-XXXX
 * International: +XX XXX XXX XXXX (preserves country code)
 */
export function formatPhoneNumber(value: string): string {
  if (!value) return value;

  const digits = value.replaceAll(/[^\d+]/g, "");

  if (digits.startsWith("+")) {
    const numberPart = digits.slice(1);
    // Determine country code length: +1 (US/CA), +XX (most), +XXX (some)
    let ccLength = 1;
    if (numberPart.startsWith("1")) {
      ccLength = 1;
    } else if (
      numberPart.length >= 3 &&
      /^(2\d{2}|3\d{2}|4\d{2}|5\d{2}|6\d{2}|7\d{2}|8\d{2}|9\d{2})/.test(
        numberPart,
      )
    ) {
      // Most non-+1 codes are 2 digits, but some are 3.
      // Use 2-digit as default for simplicity — correct for vast majority.
      ccLength = 2;
    }
    const cc = numberPart.slice(0, ccLength);
    const rest = numberPart.slice(ccLength);
    if (rest.length === 0) return `+${cc}`;
    if (rest.length <= 3) return `+${cc} ${rest}`;
    if (rest.length <= 6) return `+${cc} ${rest.slice(0, 3)} ${rest.slice(3)}`;
    return `+${cc} ${rest.slice(0, 3)} ${rest.slice(3, 6)} ${rest.slice(6, 10)}`;
  }

  if (digits.length === 11 && digits.startsWith("1")) {
    const number_ = digits.slice(1);
    return `+1 (${number_.slice(0, 3)}) ${number_.slice(3, 6)}-${number_.slice(6, 10)}`;
  }

  if (digits.length < 4) return digits;
  if (digits.length < 7) {
    return `(${digits.slice(0, 3)}) ${digits.slice(3)}`;
  }

  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 10)}`;
}

/**
 * Validates a phone number - basic validation for common formats
 * Returns true if the phone number appears valid, false otherwise
 */
export function isValidPhoneNumber(value: string): boolean {
  if (!value) return true; // Phone is optional

  // Remove all non-digit characters except +
  const cleaned = value.replaceAll(/[^\d+]/g, "");

  // Check for valid length (10-15 digits, optionally with + prefix)
  if (cleaned.startsWith("+")) {
    const numberPart = cleaned.slice(1);
    return /^\d{10,15}$/.test(numberPart);
  }

  // US number: 10 digits, or 11 digits starting with 1
  if (/^\d{10}$/.test(cleaned)) return true;
  if (/^1\d{10}$/.test(cleaned)) return true;

  // International: 10-15 digits
  return /^\d{10,15}$/.test(cleaned);
}

/**
 * Returns true if a phone number string is non-empty (i.e., actually provided).
 * Use alongside `isValidPhoneNumber` when you need to distinguish
 * "no phone given" (acceptable) from "phone given but invalid".
 */
export function isPhonePresent(value: string): boolean {
  return !!value && value.replaceAll(/[^\d+]/g, "").length > 0;
}
